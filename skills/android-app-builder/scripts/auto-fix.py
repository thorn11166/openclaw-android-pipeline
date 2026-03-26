#!/usr/bin/env python3
"""
Android Build Auto-Fix Engine

Takes error reports from error-parser.py and generates + applies automated fixes.
Modifies build.gradle.kts, gradle.properties, AndroidManifest.xml, and resource files.

Supports:
  - Dependency version updates
  - AndroidX/Jetpack configuration
  - Manifest merge issues
  - Missing resources
  - Gradle sync problems
  - SDK version mismatches

Usage:
    python auto-fix.py --error-json errors.json --project-dir . --apply
"""

import argparse
import json
import re
import sys
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class FixStrategy(Enum):
    """Available fix strategies."""
    UPDATE_DEPENDENCY = "update_dependency"
    UPDATE_GRADLE_VERSION = "update_gradle_version"
    UPDATE_SDK_VERSION = "update_sdk_version"
    ENABLE_ANDROIDX = "enable_androidx"
    ENABLE_JET_PACK = "enable_jet_pack"
    FIX_MANIFEST_MERGE = "fix_manifest_merge"
    ADD_MISSING_RESOURCE = "add_missing_resource"
    ADD_PERMISSION = "add_permission"
    FIX_KOTLIN_SYNTAX = "fix_kotlin_syntax"
    REFRESH_DEPENDENCIES = "refresh_dependencies"
    UNKNOWN = "unknown"


@dataclass
class FixSuggestion:
    """A single fix suggestion."""
    strategy: str
    file_path: str
    description: str
    changes: Dict[str, Any]
    confidence: float  # 0.0-1.0


class AndroidBuildAutoFixer:
    """Automatic fix engine for Android builds."""

    def __init__(self, project_dir: Path):
        """
        Initialize fixer.

        Args:
            project_dir: Root of Android project
        """
        self.project_dir = Path(project_dir)
        self.build_gradle = self.project_dir / "build.gradle.kts"
        self.gradle_properties = self.project_dir / "gradle.properties"
        self.manifest = self._find_manifest()
        self.changes_made: List[Tuple[str, str]] = []

    def _find_manifest(self) -> Optional[Path]:
        """Find AndroidManifest.xml in project."""
        for manifest in self.project_dir.rglob("AndroidManifest.xml"):
            return manifest
        return None

    def generate_fixes(self, error_report: Dict[str, Any]) -> List[FixSuggestion]:
        """
        Analyze error report and generate fixes.

        Args:
            error_report: JSON from error-parser.py

        Returns:
            List of FixSuggestion objects
        """
        fixes = []
        errors = error_report.get("all_errors", [])

        for error in errors:
            error_type = error.get("error_type")
            message = error.get("error_message", "")

            if error_type == "dependency_resolution":
                fixes.extend(self._fix_dependency_errors(error))
            elif error_type == "gradle_sync":
                fixes.extend(self._fix_gradle_sync(error))
            elif error_type == "missing_sdk":
                fixes.extend(self._fix_missing_sdk(error))
            elif error_type == "manifest_merge":
                fixes.extend(self._fix_manifest_merge(error))
            elif error_type == "resource_conflict":
                fixes.extend(self._fix_resource_conflicts(error))
            elif error_type == "kotlin_compilation":
                fixes.extend(self._fix_kotlin_errors(error))
            elif error_type == "java_compilation":
                fixes.extend(self._fix_java_errors(error))

        # Deduplicate fixes
        unique_fixes = self._deduplicate_fixes(fixes)
        logger.info(f"Generated {len(unique_fixes)} fix suggestions")
        return unique_fixes

    def _fix_dependency_errors(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix dependency version conflicts."""
        fixes = []
        message = error.get("error_message", "")

        # Try to extract artifact name
        artifact_match = re.search(r"([a-zA-Z0-9\-.:]+):([0-9.]+)", message)
        if artifact_match:
            artifact = artifact_match.group(1)
            version = artifact_match.group(2)

            # Suggest common AndroidX/Jetpack updates
            androidx_updates = self._get_androidx_updates(artifact)
            if androidx_updates:
                fixes.append(
                    FixSuggestion(
                        strategy=FixStrategy.UPDATE_DEPENDENCY.value,
                        file_path="build.gradle.kts",
                        description=f"Update {artifact} to compatible version",
                        changes={
                            "artifact": artifact,
                            "old_version": version,
                            "new_version": androidx_updates.get("recommended_version"),
                            "replacement": androidx_updates.get("replacement"),
                        },
                        confidence=0.85,
                    )
                )

        # If AndroidX/Jetpack related, suggest enabling flags
        if "androidx" in message.lower() or "jetpack" in message.lower():
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.ENABLE_ANDROIDX.value,
                    file_path="gradle.properties",
                    description="Enable AndroidX in gradle.properties",
                    changes={"android.useAndroidX": "true", "android.enableJetifier": "true"},
                    confidence=0.9,
                )
            )

        return fixes

    def _fix_gradle_sync(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix Gradle sync failures."""
        fixes = []
        message = error.get("error_message", "")

        # Check for common SDK version issues
        sdk_match = re.search(r"compileSdkVersion.*(\d+)", message)
        if sdk_match:
            target_sdk = int(sdk_match.group(1))
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.UPDATE_SDK_VERSION.value,
                    file_path="build.gradle.kts",
                    description=f"Update compileSdkVersion to {target_sdk}",
                    changes={
                        "compileSdkVersion": target_sdk,
                        "targetSdkVersion": target_sdk,
                    },
                    confidence=0.8,
                )
            )

        # Suggest enabling AndroidX
        if "androidx" in message.lower():
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.ENABLE_ANDROIDX.value,
                    file_path="gradle.properties",
                    description="Enable AndroidX compatibility",
                    changes={"android.useAndroidX": "true"},
                    confidence=0.7,
                )
            )

        return fixes

    def _fix_missing_sdk(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix missing SDK components."""
        fixes = []
        message = error.get("error_message", "")

        # Try to extract SDK version
        version_match = re.search(r"android-(\d+)", message)
        if version_match:
            sdk_version = int(version_match.group(1))
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.UPDATE_SDK_VERSION.value,
                    file_path="build.gradle.kts",
                    description=f"Update compileSdkVersion to Android {sdk_version}",
                    changes={"compileSdkVersion": sdk_version},
                    confidence=0.9,
                )
            )

        return fixes

    def _fix_manifest_merge(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix manifest merge conflicts."""
        fixes = []
        message = error.get("error_message", "")
        file_path = error.get("file_path")

        # Extract conflicting attribute
        attr_match = re.search(r"attribute\s+([a-zA-Z:]+)", message, re.IGNORECASE)
        if attr_match:
            attribute = attr_match.group(1)
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.FIX_MANIFEST_MERGE.value,
                    file_path=file_path or "AndroidManifest.xml",
                    description=f"Add tools:replace for {attribute} conflict",
                    changes={"attribute": attribute, "action": "tools:replace"},
                    confidence=0.75,
                )
            )

        return fixes

    def _fix_resource_conflicts(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix duplicate resource definitions."""
        fixes = []
        message = error.get("error_message", "")

        # Extract resource ID
        res_match = re.search(r"@([a-zA-Z]+)/([a-zA-Z0-9_]+)", message)
        if res_match:
            res_type = res_match.group(1)
            res_name = res_match.group(2)
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.ADD_MISSING_RESOURCE.value,
                    file_path=f"res/values/{res_type}s.xml",
                    description=f"Review and deduplicate {res_type} resource '{res_name}'",
                    changes={"resource_type": res_type, "resource_name": res_name},
                    confidence=0.6,
                )
            )

        return fixes

    def _fix_kotlin_errors(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix Kotlin compilation errors."""
        fixes = []
        message = error.get("error_message", "")
        file_path = error.get("file_path")

        # This is limited - Kotlin syntax errors are hard to auto-fix
        if "unresolved reference" in message:
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.FIX_KOTLIN_SYNTAX.value,
                    file_path=file_path or "unknown",
                    description="Check imports and verify class name spelling",
                    changes={"check": "imports and references"},
                    confidence=0.3,  # Low confidence - requires manual review
                )
            )

        return fixes

    def _fix_java_errors(self, error: Dict[str, Any]) -> List[FixSuggestion]:
        """Fix Java compilation errors."""
        fixes = []
        message = error.get("error_message", "")
        file_path = error.get("file_path")

        # Similar to Kotlin - limited auto-fix capability
        if "cannot find symbol" in message:
            fixes.append(
                FixSuggestion(
                    strategy=FixStrategy.FIX_KOTLIN_SYNTAX.value,
                    file_path=file_path or "unknown",
                    description="Check imports and class definitions",
                    changes={"check": "imports and definitions"},
                    confidence=0.3,
                )
            )

        return fixes

    def _get_androidx_updates(self, artifact: str) -> Optional[Dict[str, str]]:
        """Get recommended AndroidX updates for artifact."""
        # Common AndroidX updates mapping
        updates_map = {
            "androidx.appcompat:appcompat": {
                "recommended_version": "1.6.1",
                "replacement": None,
            },
            "androidx.cardview:cardview": {
                "recommended_version": "1.0.0",
                "replacement": None,
            },
            "androidx.recyclerview:recyclerview": {
                "recommended_version": "1.3.2",
                "replacement": None,
            },
            "androidx.constraintlayout:constraintlayout": {
                "recommended_version": "2.1.4",
                "replacement": None,
            },
            "androidx.lifecycle:lifecycle-runtime-ktx": {
                "recommended_version": "2.6.2",
                "replacement": None,
            },
            "androidx.activity:activity-ktx": {
                "recommended_version": "1.8.1",
                "replacement": None,
            },
            "androidx.fragment:fragment-ktx": {
                "recommended_version": "1.6.2",
                "replacement": None,
            },
            "com.google.android.material:material": {
                "recommended_version": "1.10.0",
                "replacement": None,
            },
        }

        for key, value in updates_map.items():
            if key == artifact:
                return value

        return None

    def _deduplicate_fixes(self, fixes: List[FixSuggestion]) -> List[FixSuggestion]:
        """Remove duplicate fix suggestions, keeping highest confidence."""
        seen = {}
        for fix in fixes:
            key = (fix.strategy, fix.file_path)
            if key not in seen or fix.confidence > seen[key].confidence:
                seen[key] = fix
        return list(seen.values())

    def apply_fixes(self, fixes: List[FixSuggestion]) -> Tuple[int, List[str]]:
        """
        Apply fixes to project files.

        Args:
            fixes: List of FixSuggestion objects

        Returns:
            Tuple of (number_of_changes_made, list_of_change_descriptions)
        """
        changes_made = []

        for fix in fixes:
            logger.info(f"Applying: {fix.description}")

            if fix.strategy == FixStrategy.UPDATE_DEPENDENCY.value:
                if self._apply_dependency_update(fix):
                    changes_made.append(f"✅ Updated {fix.changes.get('artifact')}")

            elif fix.strategy == FixStrategy.UPDATE_SDK_VERSION.value:
                if self._apply_sdk_version_update(fix):
                    changes_made.append(f"✅ Updated SDK version")

            elif fix.strategy == FixStrategy.ENABLE_ANDROIDX.value:
                if self._apply_androidx_enablement(fix):
                    changes_made.append(f"✅ Enabled AndroidX")

            elif fix.strategy == FixStrategy.FIX_MANIFEST_MERGE.value:
                if self._apply_manifest_fix(fix):
                    changes_made.append(f"✅ Fixed manifest merge")

            elif fix.strategy == FixStrategy.ADD_MISSING_RESOURCE.value:
                logger.warning(f"⚠️  Manual review needed: {fix.description}")
                changes_made.append(f"⚠️  Review needed: {fix.description}")

            elif fix.strategy == FixStrategy.FIX_KOTLIN_SYNTAX.value:
                logger.warning(f"⚠️  Manual review needed: {fix.description}")
                changes_made.append(f"⚠️  Review needed: {fix.description}")

        logger.info(f"Applied {len(changes_made)} changes")
        return len(changes_made), changes_made

    def _apply_dependency_update(self, fix: FixSuggestion) -> bool:
        """Update dependency in build.gradle.kts."""
        if not self.build_gradle.exists():
            logger.warning("build.gradle.kts not found")
            return False

        content = self.build_gradle.read_text()
        artifact = fix.changes.get("artifact")
        old_version = fix.changes.get("old_version")
        new_version = fix.changes.get("new_version")

        # Try to find and replace the dependency
        pattern = rf'(\s*(?:implementation|api|testImplementation)\s*\(\s*["\']){artifact}:[0-9.]+(["\']\s*\))'
        replacement = rf'\1{artifact}:{new_version}\2'

        updated_content = re.sub(pattern, replacement, content)

        if updated_content != content:
            self.build_gradle.write_text(updated_content)
            logger.info(f"Updated {artifact} to {new_version}")
            return True

        logger.warning(f"Could not find dependency pattern for {artifact}:{old_version} in build.gradle.kts")
        return False

    def _apply_sdk_version_update(self, fix: FixSuggestion) -> bool:
        """Update SDK versions in build.gradle.kts."""
        if not self.build_gradle.exists():
            logger.warning("build.gradle.kts not found")
            return False

        content = self.build_gradle.read_text()
        compile_sdk = fix.changes.get("compileSdkVersion")
        target_sdk = fix.changes.get("targetSdkVersion", compile_sdk)

        updated = False

        if compile_sdk:
            pattern = r'compileSdk\s*=\s*\d+'
            replacement = f'compileSdk = {compile_sdk}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
                logger.info(f"Updated compileSdk to {compile_sdk}")

        if target_sdk:
            pattern = r'targetSdk\s*=\s*\d+'
            replacement = f'targetSdk = {target_sdk}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
                logger.info(f"Updated targetSdk to {target_sdk}")

        if updated:
            self.build_gradle.write_text(content)
            return True

        return False

    def _apply_androidx_enablement(self, fix: FixSuggestion) -> bool:
        """Enable AndroidX in gradle.properties."""
        if not self.gradle_properties.exists():
            logger.warning("gradle.properties not found, creating...")
            self.gradle_properties.parent.mkdir(parents=True, exist_ok=True)
            self.gradle_properties.write_text("")

        content = self.gradle_properties.read_text()
        updated = False

        for key, value in fix.changes.items():
            pattern = rf'^{re.escape(key)}\s*=.*$'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, f'{key}={value}', content, flags=re.MULTILINE)
            else:
                content += f'\n{key}={value}\n'
            updated = True
            logger.info(f"Set {key}={value}")

        if updated:
            self.gradle_properties.write_text(content)
            return True

        return False

    def _apply_manifest_fix(self, fix: FixSuggestion) -> bool:
        """Fix manifest merge conflicts."""
        if not self.manifest or not self.manifest.exists():
            logger.warning("AndroidManifest.xml not found")
            return False

        content = self.manifest.read_text()
        attribute = fix.changes.get("attribute")

        # Add tools namespace if missing
        if 'xmlns:tools="http://schemas.android.com/tools"' not in content:
            content = content.replace(
                '<manifest',
                '<manifest xmlns:tools="http://schemas.android.com/tools"',
            )
            logger.info("Added tools namespace to manifest")

        # Note: Adding tools:replace requires knowing the exact element
        # This is a placeholder for manual review
        logger.warning(f"Manual review needed: add tools:replace for {attribute}")
        return False

    def get_summary(self) -> str:
        """Get summary of fixes applied."""
        summary = f"""
╔═══════════════════════════════════════════════════════╗
║          AUTO-FIX SUMMARY                             ║
╠═══════════════════════════════════════════════════════╣
║ Changes Made: {len(self.changes_made)}
║ Timestamp: {datetime.now().isoformat()}
║───────────────────────────────────────────────────────║
"""
        for file, change in self.changes_made:
            summary += f"║ {file}: {change}\n"
        summary += "╚═══════════════════════════════════════════════════════╝"
        return summary


def main():
    parser = argparse.ArgumentParser(description="Android build auto-fix engine")
    parser.add_argument(
        "--error-json",
        required=True,
        help="Path to error-parser.py JSON output",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of Android project (default: .)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes (default: preview only)",
    )
    parser.add_argument(
        "--output-json",
        help="Write fix suggestions to JSON file",
    )

    args = parser.parse_args()

    # Load error report
    error_file = Path(args.error_json)
    if not error_file.exists():
        logger.error(f"Error file not found: {error_file}")
        sys.exit(1)

    try:
        error_report = json.loads(error_file.read_text())
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        sys.exit(1)

    # Initialize fixer
    fixer = AndroidBuildAutoFixer(args.project_dir)

    # Generate fixes
    fixes = fixer.generate_fixes(error_report)

    if not fixes:
        logger.info("No fixes generated")
        sys.exit(0)

    # Display fixes
    logger.info("=" * 60)
    logger.info("FIX SUGGESTIONS")
    logger.info("=" * 60)

    for i, fix in enumerate(fixes, 1):
        logger.info(f"\n{i}. {fix.description}")
        logger.info(f"   Strategy: {fix.strategy}")
        logger.info(f"   File: {fix.file_path}")
        logger.info(f"   Confidence: {fix.confidence * 100:.0f}%")

    # Write JSON if requested
    if args.output_json:
        output = {
            "total_suggestions": len(fixes),
            "timestamp": datetime.now().isoformat(),
            "suggestions": [
                {
                    "strategy": f.strategy,
                    "file": f.file_path,
                    "description": f.description,
                    "confidence": f.confidence,
                    "changes": f.changes,
                }
                for f in fixes
            ],
        }
        Path(args.output_json).write_text(json.dumps(output, indent=2))
        logger.info(f"\n✅ Fixes written to {args.output_json}")

    # Apply if requested
    if args.apply:
        logger.info("\n" + "=" * 60)
        logger.info("APPLYING FIXES")
        logger.info("=" * 60 + "\n")

        count, changes = fixer.apply_fixes(fixes)
        logger.info(f"\nApplied {count} fix(es)")

        for change in changes:
            logger.info(f"  {change}")

        sys.exit(0)
    else:
        logger.info("\n(Use --apply to apply fixes)")
        sys.exit(0)


if __name__ == "__main__":
    main()
