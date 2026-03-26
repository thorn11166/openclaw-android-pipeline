#!/usr/bin/env python3
"""
Claude Code Reviewer for Android Projects

Reviews AI-generated Android/Kotlin source code using the Claude API and
produces a structured report with actionable suggestions. The key output is
`prompt_for_model` — a ready-to-use prompt that can be fed directly back to
the code-generating model (e.g. DeepSeek) so it can revise its own output
before the code is ever pushed to GitHub.

Fits into the android-app-builder skill as Phase 2.5, between code generation
and GitHub integration.

Usage:
    python code-reviewer.py \\
        --project-dir /path/to/android/project \\
        --api-key $ANTHROPIC_API_KEY \\
        --output-json .code-review-report.json

    # Higher-quality review with Opus:
    python code-reviewer.py \\
        --project-dir . \\
        --api-key $ANTHROPIC_API_KEY \\
        --model claude-opus-4-6 \\
        --output-json .code-review-report.json

    # Only fail on critical issues:
    python code-reviewer.py \\
        --project-dir . \\
        --api-key $ANTHROPIC_API_KEY \\
        --pass-threshold 0
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"

# Files/directories to skip
SKIP_DIRS = {
    "build", ".gradle", ".idea", "__pycache__", "node_modules",
    "intermediates", "generated", "outputs", ".git",
}
SKIP_FILES = {"gradlew", "gradlew.bat"}
REVIEW_EXTENSIONS = {".kt", ".java", ".xml", ".kts"}

# Skip files larger than this (bytes) — avoids token limits on generated code
MAX_FILE_BYTES = 40_000


class AndroidCodeReviewer:
    """Reviews Android project source files using the Claude API."""

    def __init__(
        self,
        project_dir: str,
        api_key: str,
        model: str = DEFAULT_MODEL,
        pass_threshold: int = 60,
    ):
        """
        Args:
            project_dir: Root of the Android project to review.
            api_key: Anthropic API key.
            model: Claude model ID to use for reviews.
            pass_threshold: Minimum quality score (0–100) to consider the
                review passed. Reviews below this score set exit code 1.
        """
        self.project_dir = Path(project_dir).resolve()
        self.api_key = api_key
        self.model = model
        self.pass_threshold = pass_threshold

    # ------------------------------------------------------------------
    # File collection
    # ------------------------------------------------------------------

    def _should_skip(self, path: Path) -> bool:
        """Return True if this path should be excluded from review."""
        for part in path.parts:
            if part in SKIP_DIRS:
                return True
        if path.name in SKIP_FILES:
            return True
        if path.stat().st_size > MAX_FILE_BYTES:
            logger.warning(f"Skipping large file ({path.stat().st_size} bytes): {path.name}")
            return True
        return False

    def collect_source_files(self) -> Dict[str, str]:
        """
        Walk the project directory and collect all reviewable source files.

        Returns:
            Dict mapping relative file path → file content.
        """
        files: Dict[str, str] = {}

        for ext in REVIEW_EXTENSIONS:
            for fpath in sorted(self.project_dir.rglob(f"*{ext}")):
                rel = fpath.relative_to(self.project_dir)
                if self._should_skip(fpath):
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                    files[str(rel)] = content
                except Exception as e:
                    logger.warning(f"Could not read {rel}: {e}")

        logger.info(f"Collected {len(files)} source file(s) for review")
        return files

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(self, source_files: Dict[str, str]) -> str:
        """Build the review prompt to send to Claude."""
        files_block = "\n\n".join(
            f"### {path}\n```\n{content}\n```"
            for path, content in source_files.items()
        )

        return f"""You are performing a code review of Android/Kotlin source files generated \
by a cheaper AI model (DeepSeek). Your goal is to catch problems before the code is pushed \
to GitHub and compiled — saving CI/CD time and cost.

Review for these categories (in priority order):
1. **critical** — Will definitely prevent the project from building (missing class, \
bad XML tag, unresolved reference, wrong package name, missing resource, etc.)
2. **high** — Likely runtime crash or serious architecture violation (wrong theme \
for setSupportActionBar, memory leak, blocking the main thread, etc.)
3. **medium** — Best-practice violations that cause bugs or maintainability issues \
(hardcoded strings outside strings.xml, missing null checks, misused lifecycle, etc.)
4. **low** — Style and minor improvements (naming conventions, redundant imports, etc.)

Also note:
- Security: hardcoded API keys or passwords, `android:debuggable="true"` in release, \
cleartext traffic enabled without justification
- Resources: @string/@color/@drawable references that don't exist in values files
- Gradle: dependency version conflicts, deprecated APIs

Output ONLY valid JSON, with no markdown fencing, matching this exact schema:
{{
  "overall_quality": "poor | fair | good | excellent",
  "quality_score": <integer 0-100>,
  "summary": "<1-2 sentence overall assessment>",
  "issues": [
    {{
      "severity": "critical | high | medium | low",
      "category": "build | architecture | resources | security | performance | style",
      "file": "<relative file path>",
      "line": <integer or null>,
      "issue": "<clear description of the problem>",
      "suggestion": "<concrete fix, including replacement code snippet where possible>"
    }}
  ],
  "prompt_for_model": "<A complete, self-contained prompt addressed directly to the \
code-generating model, listing every critical and high issue with the exact change \
required. Written in imperative form: 'In MainActivity.kt line 17, replace X with Y \
because Z.' Should be copy-pasteable as the next instruction to DeepSeek.>"
}}

If there are no issues, set issues to [] and prompt_for_model to "".

Source files to review:

{files_block}"""

    # ------------------------------------------------------------------
    # Claude API call
    # ------------------------------------------------------------------

    def _call_claude(self, prompt: str) -> Dict:
        """
        Send the prompt to the Claude API and return the parsed JSON response.

        Raises:
            requests.HTTPError: On non-2xx response.
            json.JSONDecodeError: If Claude's reply isn't parseable JSON.
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        logger.info(f"Sending review request to Claude ({self.model})...")
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        raw = response.json()
        text = raw["content"][0]["text"].strip()

        # Strip markdown fencing if Claude adds it despite instructions
        if text.startswith("```"):
            lines = text.splitlines()
            # Remove opening fence (```json or ```)
            lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        return json.loads(text)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict:
        """
        Collect source files, run the Claude review, and return a complete
        review report dict.
        """
        source_files = self.collect_source_files()

        if not source_files:
            logger.warning("No source files found to review")
            return {
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model,
                "project_dir": str(self.project_dir),
                "reviewed_files": [],
                "overall_quality": "unknown",
                "quality_score": 0,
                "summary": "No reviewable source files found in project directory.",
                "issues": [],
                "issue_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "prompt_for_model": "",
                "passed": False,
            }

        prompt = self._build_prompt(source_files)
        review = self._call_claude(prompt)

        # Normalise and enrich the report
        issues = review.get("issues", [])
        counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in issues:
            sev = issue.get("severity", "low")
            if sev in counts:
                counts[sev] += 1

        quality_score = int(review.get("quality_score", 0))
        passed = (
            quality_score >= self.pass_threshold
            and counts["critical"] == 0
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model,
            "project_dir": str(self.project_dir),
            "reviewed_files": list(source_files.keys()),
            "overall_quality": review.get("overall_quality", "unknown"),
            "quality_score": quality_score,
            "summary": review.get("summary", ""),
            "issues": issues,
            "issue_counts": counts,
            "prompt_for_model": review.get("prompt_for_model", ""),
            "passed": passed,
        }

        return report


# ------------------------------------------------------------------
# Reporting helpers
# ------------------------------------------------------------------

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}

QUALITY_EMOJI = {
    "poor": "❌",
    "fair": "⚠️ ",
    "good": "✅",
    "excellent": "🌟",
}


def print_report(report: Dict) -> None:
    """Pretty-print the review report to stdout."""
    q = report.get("overall_quality", "unknown")
    emoji = QUALITY_EMOJI.get(q, "❓")
    score = report.get("quality_score", 0)
    counts = report.get("issue_counts", {})

    print(f"\n{'=' * 60}")
    print(f"  CODE REVIEW REPORT")
    print(f"{'=' * 60}")
    print(f"  Quality : {emoji} {q.upper()} ({score}/100)")
    print(f"  Summary : {report.get('summary', '')}")
    print(f"  Issues  : 🔴 {counts.get('critical', 0)} critical  "
          f"🟠 {counts.get('high', 0)} high  "
          f"🟡 {counts.get('medium', 0)} medium  "
          f"🔵 {counts.get('low', 0)} low")
    print(f"  Files   : {len(report.get('reviewed_files', []))} reviewed")
    print(f"  Passed  : {'✅ YES' if report.get('passed') else '❌ NO'}")
    print(f"{'=' * 60}\n")

    issues = report.get("issues", [])
    if issues:
        # Show critical and high first
        for sev in ("critical", "high", "medium", "low"):
            section = [i for i in issues if i.get("severity") == sev]
            if not section:
                continue
            print(f"{'─' * 60}")
            print(f"  {SEVERITY_EMOJI.get(sev, '')} {sev.upper()} ISSUES ({len(section)})")
            print(f"{'─' * 60}")
            for issue in section:
                loc = issue.get("file", "")
                if issue.get("line"):
                    loc += f":{issue['line']}"
                print(f"\n  [{issue.get('category', '').upper()}] {loc}")
                print(f"  Problem    : {issue.get('issue', '')}")
                print(f"  Suggestion : {issue.get('suggestion', '')}")
        print()

    if report.get("prompt_for_model"):
        print(f"{'─' * 60}")
        print("  PROMPT FOR CODE-GENERATING MODEL")
        print(f"{'─' * 60}")
        print(f"\n{report['prompt_for_model']}\n")


def send_discord_summary(report: Dict, webhook_url: str) -> None:
    """Post a summary embed to Discord."""
    q = report.get("overall_quality", "unknown")
    score = report.get("quality_score", 0)
    counts = report.get("issue_counts", {})
    passed = report.get("passed", False)

    color = 0x2ECC71 if passed else (0xE74C3C if counts.get("critical", 0) > 0 else 0xF39C12)
    title = f"{'✅' if passed else '❌'} Code Review — {q.upper()} ({score}/100)"

    fields = [
        {
            "name": "Issues Found",
            "value": (
                f"🔴 {counts.get('critical', 0)} critical\n"
                f"🟠 {counts.get('high', 0)} high\n"
                f"🟡 {counts.get('medium', 0)} medium\n"
                f"🔵 {counts.get('low', 0)} low"
            ),
            "inline": True,
        },
        {
            "name": "Files Reviewed",
            "value": str(len(report.get("reviewed_files", []))),
            "inline": True,
        },
        {
            "name": "Reviewer Model",
            "value": report.get("model_used", "unknown"),
            "inline": True,
        },
    ]

    if report.get("summary"):
        fields.append({
            "name": "Summary",
            "value": report["summary"][:1024],
            "inline": False,
        })

    # Show critical issues inline if any
    critical = [i for i in report.get("issues", []) if i.get("severity") == "critical"]
    if critical:
        issue_lines = []
        for i in critical[:5]:  # cap at 5
            loc = i.get("file", "")
            if i.get("line"):
                loc += f":{i['line']}"
            issue_lines.append(f"• `{loc}` — {i.get('issue', '')[:80]}")
        fields.append({
            "name": f"🔴 Critical Issues ({len(critical)})",
            "value": "\n".join(issue_lines)[:1024],
            "inline": False,
        })

    payload = {
        "embeds": [{
            "title": title,
            "description": "Claude reviewed the AI-generated code before it was pushed to GitHub.",
            "color": color,
            "fields": fields,
            "timestamp": report.get("timestamp", datetime.utcnow().isoformat()) + "Z",
        }]
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("✅ Discord review summary sent")
    except Exception as e:
        logger.warning(f"Failed to send Discord notification: {e}")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review AI-generated Android code using the Claude API"
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root of the Android project to review (default: .)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("ANTHROPIC_API_KEY"),
        help="Anthropic API key (or ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output-json",
        help="Write full report to this JSON file",
    )
    parser.add_argument(
        "--pass-threshold",
        type=int,
        default=60,
        help="Minimum quality score (0–100) to exit 0. "
             "Critical issues always fail regardless. (default: 60)",
    )
    parser.add_argument(
        "--discord-webhook",
        default=os.getenv("DISCORD_WEBHOOK_URL"),
        help="Discord webhook URL for summary notification (optional)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the formatted console report",
    )

    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: Anthropic API key required. Set ANTHROPIC_API_KEY or use --api-key")
        sys.exit(1)

    reviewer = AndroidCodeReviewer(
        project_dir=args.project_dir,
        api_key=args.api_key,
        model=args.model,
        pass_threshold=args.pass_threshold,
    )

    try:
        report = reviewer.run()
    except requests.HTTPError as e:
        logger.error(f"Claude API error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text[:500]}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned non-JSON output: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

    # Console output
    if not args.quiet:
        print_report(report)

    # Save JSON
    if args.output_json:
        out = Path(args.output_json)
        out.write_text(json.dumps(report, indent=2))
        logger.info(f"✅ Review report saved: {out}")

    # Discord
    if args.discord_webhook:
        send_discord_summary(report, args.discord_webhook)

    # Exit code: 0 = passed, 1 = failed
    sys.exit(0 if report.get("passed") else 1)


if __name__ == "__main__":
    main()
