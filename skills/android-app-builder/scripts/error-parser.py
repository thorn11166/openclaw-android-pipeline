#!/usr/bin/env python3
"""
Android Build Error Parser

Extracts meaningful errors from Gradle/Kotlin build logs and categorizes them.
Provides suggestions for fixes based on error type.

Usage:
    python error-parser.py --log-file build-logs/run-12345.log --output-format json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class ErrorType(Enum):
    """Categorized Android build errors."""

    GRADLE_SYNC = "gradle_sync"
    MISSING_SDK = "missing_sdk"
    KOTLIN_COMPILATION = "kotlin_compilation"
    JAVA_COMPILATION = "java_compilation"
    RESOURCE_CONFLICT = "resource_conflict"
    MANIFEST_MERGE = "manifest_merge"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    BUILD_TIMEOUT = "build_timeout"
    UNKNOWN = "unknown"


@dataclass
class ParsedError:
    """Structured error information."""

    error_type: str
    line_number: Optional[int]
    file_path: Optional[str]
    error_message: str
    suggestion: str
    raw_context: str


class AndroidBuildErrorParser:
    """Parse Android build logs for errors."""

    # Error patterns
    PATTERNS = {
        ErrorType.GRADLE_SYNC: [
            r"Failed to resolve dependency",
            r"Gradle sync failed",
            r"FAILURE: Build failed with an exception",
            r"Could not resolve all files for configuration",
        ],
        ErrorType.MISSING_SDK: [
            r"compileSdkVersion.*is not installed",
            r"Build tools version.*is not available",
            r"Android SDK.*not found",
            r"SDK location not found",
        ],
        ErrorType.KOTLIN_COMPILATION: [
            r"error: (.+) cannot be called with arguments",
            r"error: unresolved reference",
            r"Type mismatch",
            r"Incompatible types",
            r"not callable as function",
        ],
        ErrorType.JAVA_COMPILATION: [
            r"error: (.+) cannot find symbol",
            r"error: package (.+) does not exist",
            r"error: (.+) is abstract; cannot be instantiated",
        ],
        ErrorType.RESOURCE_CONFLICT: [
            r"Duplicate resources",
            r"resource (.+) is defined multiple times",
            r"Multiple substitutions for id @",
        ],
        ErrorType.MANIFEST_MERGE: [
            r"Manifest merger failed",
            r"uses-permission (.+) conflicts",
            r"Activity (.+) already defined in",
        ],
        ErrorType.DEPENDENCY_RESOLUTION: [
            r"Dependency (.+) conflicts with another",
            r"version conflict with",
            r"No solution found",
        ],
        ErrorType.BUILD_TIMEOUT: [
            r"Build timed out",
            r"Process.*timed out",
        ],
    }

    def __init__(self, log_text: str):
        self.log = log_text
        self.lines = log_text.split("\n")

    def parse(self) -> List[ParsedError]:
        """
        Parse log and extract errors.

        Returns:
            List of ParsedError objects
        """
        errors = []

        for line_num, line in enumerate(self.lines, 1):
            error_type = self._classify_line(line)

            if error_type != ErrorType.UNKNOWN:
                error = ParsedError(
                    error_type=error_type.value,
                    line_number=line_num,
                    file_path=self._extract_file_path(line),
                    error_message=self._clean_error_message(line),
                    suggestion=self._get_suggestion(error_type, line),
                    raw_context=self._get_context(line_num),
                )
                errors.append(error)

        return errors

    def _classify_line(self, line: str) -> ErrorType:
        """Classify a line as a specific error type."""
        for error_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return error_type
        return ErrorType.UNKNOWN

    def _extract_file_path(self, line: str) -> Optional[str]:
        """Extract file path from error line."""
        match = re.search(r"(?:at|in|from|file:\/\/)?([a-zA-Z0-9_\-./\\]+\.(?:kt|java|xml))",
                          line)
        return match.group(1) if match else None

    def _clean_error_message(self, line: str) -> str:
        """Clean and normalize error message."""
        # Remove ANSI color codes
        cleaned = re.sub(r"\x1b\[[0-9;]*m", "", line)
        # Remove duplicate whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:200]  # Limit to 200 chars

    def _get_suggestion(self, error_type: ErrorType, line: str) -> str:
        """Generate suggestion based on error type."""
        suggestions = {
            ErrorType.GRADLE_SYNC: (
                "Check build.gradle.kts for missing or incorrect dependency versions. "
                "Try: ./gradlew --refresh-dependencies clean build"
            ),
            ErrorType.MISSING_SDK: (
                "Install the required Android SDK version. "
                "Use Android Studio SDK Manager or: sdkmanager 'platforms;android-XX'"
            ),
            ErrorType.KOTLIN_COMPILATION: (
                "Check Kotlin syntax and types. Verify function signatures and imports. "
                "Run: ./gradlew compileDebugKotlin for detailed errors."
            ),
            ErrorType.JAVA_COMPILATION: (
                "Check Java syntax and imports. Verify class names and packages. "
                "Run: ./gradlew compileDebugJava for detailed errors."
            ),
            ErrorType.RESOURCE_CONFLICT: (
                "Remove duplicate resource definitions. Check res/values/, res/layout/, etc. "
                "Ensure all IDs are unique across your project."
            ),
            ErrorType.MANIFEST_MERGE: (
                "Review AndroidManifest.xml for conflicts. Check library manifests. "
                "Use tools:replace or tools:ignore for intentional overrides."
            ),
            ErrorType.DEPENDENCY_RESOLUTION: (
                "Update dependency versions in build.gradle.kts. "
                "Use constraint resolution: implementation('group:artifact:latestVersion')"
            ),
            ErrorType.BUILD_TIMEOUT: (
                "Build took too long. Increase timeout in GitHub Actions workflow. "
                "Enable Gradle caching or reduce task parallelism."
            ),
            ErrorType.UNKNOWN: "Review full log for error context.",
        }
        return suggestions.get(error_type, "Check logs for details.")

    def _get_context(self, line_num: int, context_lines: int = 2) -> str:
        """Get surrounding context lines."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(self.lines), line_num + context_lines)
        context = "\n".join(self.lines[start:end])
        return context

    def summary(self) -> Dict[str, Any]:
        """
        Generate summary of all errors found.

        Returns:
            Dict with error count and grouping by type
        """
        errors = self.parse()
        by_type = {}

        for error in errors:
            error_type = error.error_type
            if error_type not in by_type:
                by_type[error_type] = []
            by_type[error_type].append(error)

        return {
            "total_errors": len(errors),
            "errors_by_type": {k: len(v) for k, v in by_type.items()},
            "first_error": asdict(errors[0]) if errors else None,
            "all_errors": [asdict(e) for e in errors],
        }


def main():
    parser = argparse.ArgumentParser(description="Parse Android build logs for errors")
    parser.add_argument("--log-file", required=True, help="Path to build log file")
    parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show error summary, not detailed errors",
    )

    args = parser.parse_args()

    log_file = Path(args.log_file)
    if not log_file.exists():
        print(f"ERROR: Log file not found: {log_file}")
        sys.exit(1)

    log_text = log_file.read_text()
    error_parser = AndroidBuildErrorParser(log_text)
    summary = error_parser.summary()

    if args.output_format == "json":
        if args.summary_only:
            # Only show counts and first error
            summary_only = {
                "total_errors": summary["total_errors"],
                "errors_by_type": summary["errors_by_type"],
                "first_error": summary["first_error"],
            }
            print(json.dumps(summary_only, indent=2))
        else:
            print(json.dumps(summary, indent=2))
    else:
        # Text output
        print(f"\n{'=' * 70}")
        print(f"Build Error Analysis: {log_file}")
        print(f"{'=' * 70}\n")

        print(f"📊 Total Errors Found: {summary['total_errors']}\n")

        if summary["errors_by_type"]:
            print("📋 Errors by Type:")
            for error_type, count in summary["errors_by_type"].items():
                print(f"  • {error_type}: {count}")
            print()

        if summary["first_error"]:
            err = summary["first_error"]
            print(f"🚨 First Error (line {err['line_number']}):")
            print(f"  Type: {err['error_type']}")
            if err["file_path"]:
                print(f"  File: {err['file_path']}")
            print(f"  Message: {err['error_message']}")
            print(f"  💡 Suggestion: {err['suggestion']}\n")

        print(f"📝 Full log: {log_file}")
        print(f"{'=' * 70}\n")

    # Exit with error code if errors found
    sys.exit(1 if summary["total_errors"] > 0 else 0)


if __name__ == "__main__":
    main()
