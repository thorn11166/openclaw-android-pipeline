#!/usr/bin/env python3
"""
Claude Code Reviewer for Android Projects

Reviews AI-generated Android/Kotlin source code using the `claude` CLI
(your existing subscription — no separate API key needed) and produces a
structured report with actionable suggestions.

The key output is `prompt_for_model` — a ready-to-use prompt that can be fed
directly back to the code-generating model (e.g. DeepSeek) so it can revise
its own output before the code is ever pushed to GitHub.

Fits into the android-app-builder skill as Phase 2.5, between code generation
and GitHub integration.

Backend selection (in priority order):
  1. `claude` CLI  — uses your existing subscription, no extra credentials
  2. Anthropic API — fallback if CLI is not on PATH (requires --api-key or
                     ANTHROPIC_API_KEY env var)

Usage:
    # Default (Sonnet via CLI subscription):
    python code-reviewer.py --project-dir /path/to/project

    # Opus via CLI subscription:
    python code-reviewer.py --project-dir . --model claude-opus-4-6

    # API key fallback:
    python code-reviewer.py --project-dir . --api-key $ANTHROPIC_API_KEY
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# requests is only needed for Discord notifications — don't hard-fail without it
try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"

SKIP_DIRS = {
    "build", ".gradle", ".idea", "__pycache__", "node_modules",
    "intermediates", "generated", "outputs", ".git",
}
SKIP_FILES = {"gradlew", "gradlew.bat"}
REVIEW_EXTENSIONS = {".kt", ".java", ".xml", ".kts"}
MAX_FILE_BYTES = 40_000  # skip files larger than this


# ---------------------------------------------------------------------------
# Core reviewer
# ---------------------------------------------------------------------------

class AndroidCodeReviewer:
    """Reviews Android project source files using Claude (CLI or API)."""

    def __init__(
        self,
        project_dir: str,
        model: str = DEFAULT_MODEL,
        pass_threshold: int = 60,
        api_key: Optional[str] = None,
    ):
        """
        Args:
            project_dir:    Root of the Android project to review.
            model:          Claude model ID passed to the CLI / API.
            pass_threshold: Minimum quality score (0–100) to pass; critical
                            issues always fail regardless of score.
            api_key:        Anthropic API key — only used if the `claude` CLI
                            is not available on PATH.
        """
        self.project_dir = Path(project_dir).resolve()
        self.model = model
        self.pass_threshold = pass_threshold
        self.api_key = api_key
        self._use_cli = shutil.which("claude") is not None

        if self._use_cli:
            logger.info(f"Backend: claude CLI  (model: {self.model})")
        elif self.api_key:
            logger.info(f"Backend: Anthropic API  (model: {self.model})")
        else:
            logger.error(
                "Neither the `claude` CLI nor an API key is available. "
                "Install Claude Code or set ANTHROPIC_API_KEY."
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # File collection
    # ------------------------------------------------------------------

    def _should_skip(self, path: Path) -> bool:
        for part in path.parts:
            if part in SKIP_DIRS:
                return True
        if path.name in SKIP_FILES:
            return True
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            logger.warning(f"Skipping large file ({size} bytes): {path.name}")
            return True
        return False

    def collect_source_files(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        for ext in REVIEW_EXTENSIONS:
            for fpath in sorted(self.project_dir.rglob(f"*{ext}")):
                rel = fpath.relative_to(self.project_dir)
                if self._should_skip(fpath):
                    continue
                try:
                    files[str(rel)] = fpath.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    logger.warning(f"Could not read {rel}: {e}")
        logger.info(f"Collected {len(files)} source file(s) for review")
        return files

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------

    def _build_prompt(self, source_files: Dict[str, str]) -> str:
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

Also check:
- Security: hardcoded API keys or passwords, `android:debuggable="true"` in release, \
cleartext traffic enabled without justification
- Resources: @string/@color/@drawable references that don't exist in the values files
- Gradle: dependency version conflicts, deprecated APIs

Output ONLY valid JSON, no markdown fencing, matching this exact schema:
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
  "prompt_for_model": "<Complete, self-contained prompt addressed directly to the \
code-generating model, listing every critical and high issue with the exact change \
required. Imperative form: 'In MainActivity.kt line 17, replace X with Y because Z.' \
Copy-pasteable as the next instruction to DeepSeek. Empty string if no issues.>"
}}

Source files to review:

{files_block}"""

    # ------------------------------------------------------------------
    # Backend: claude CLI
    # ------------------------------------------------------------------

    def _call_via_cli(self, prompt: str) -> Dict:
        """Invoke the `claude` CLI in non-interactive print mode."""
        # Write prompt to a temp file to avoid shell argument-length limits
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(prompt)
            tmp_path = tmp.name

        try:
            logger.info(f"Running: claude -p <prompt> --model {self.model}")
            result = subprocess.run(
                ["claude", "--model", self.model, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=180,
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if result.returncode != 0:
            raise RuntimeError(
                f"claude CLI exited {result.returncode}: {result.stderr[:500]}"
            )

        return self._parse_json_response(result.stdout)

    # ------------------------------------------------------------------
    # Backend: Anthropic API (fallback)
    # ------------------------------------------------------------------

    def _call_via_api(self, prompt: str) -> Dict:
        """Call the Anthropic messages API directly."""
        if not _REQUESTS_AVAILABLE:
            raise RuntimeError(
                "requests library required for API mode. "
                "Install with: pip install requests"
            )
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
        logger.info(f"Calling Anthropic API (model: {self.model})...")
        resp = _requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return self._parse_json_response(resp.json()["content"][0]["text"])

    # ------------------------------------------------------------------
    # Shared response parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_response(text: str) -> Dict:
        text = text.strip()
        # Strip markdown fencing if present
        if text.startswith("```"):
            lines = text.splitlines()[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return json.loads(text)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> Dict:
        source_files = self.collect_source_files()

        if not source_files:
            logger.warning("No source files found to review")
            return _empty_report(self.model, str(self.project_dir))

        prompt = self._build_prompt(source_files)
        review = self._call_via_cli(prompt) if self._use_cli else self._call_via_api(prompt)

        issues = review.get("issues", [])
        counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in issues:
            sev = issue.get("severity", "low")
            if sev in counts:
                counts[sev] += 1

        quality_score = int(review.get("quality_score", 0))
        passed = quality_score >= self.pass_threshold and counts["critical"] == 0

        return {
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model,
            "backend": "cli" if self._use_cli else "api",
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


def _empty_report(model: str, project_dir: str) -> Dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "model_used": model,
        "backend": "n/a",
        "project_dir": project_dir,
        "reviewed_files": [],
        "overall_quality": "unknown",
        "quality_score": 0,
        "summary": "No reviewable source files found in project directory.",
        "issues": [],
        "issue_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "prompt_for_model": "",
        "passed": False,
    }


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
QUALITY_EMOJI  = {"poor": "❌", "fair": "⚠️ ", "good": "✅", "excellent": "🌟"}


def print_report(report: Dict) -> None:
    q      = report.get("overall_quality", "unknown")
    score  = report.get("quality_score", 0)
    counts = report.get("issue_counts", {})

    print(f"\n{'=' * 60}")
    print(f"  CODE REVIEW REPORT")
    print(f"{'=' * 60}")
    print(f"  Quality : {QUALITY_EMOJI.get(q, '❓')} {q.upper()} ({score}/100)")
    print(f"  Backend : {report.get('backend', 'unknown')}  "
          f"(model: {report.get('model_used', '')})")
    print(f"  Summary : {report.get('summary', '')}")
    print(f"  Issues  : 🔴 {counts.get('critical', 0)} critical  "
          f"🟠 {counts.get('high', 0)} high  "
          f"🟡 {counts.get('medium', 0)} medium  "
          f"🔵 {counts.get('low', 0)} low")
    print(f"  Files   : {len(report.get('reviewed_files', []))} reviewed")
    print(f"  Passed  : {'✅ YES' if report.get('passed') else '❌ NO'}")
    print(f"{'=' * 60}\n")

    for sev in ("critical", "high", "medium", "low"):
        section = [i for i in report.get("issues", []) if i.get("severity") == sev]
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
    if not _REQUESTS_AVAILABLE:
        logger.warning("requests not installed — skipping Discord notification")
        return

    q      = report.get("overall_quality", "unknown")
    score  = report.get("quality_score", 0)
    counts = report.get("issue_counts", {})
    passed = report.get("passed", False)

    color = 0x2ECC71 if passed else (0xE74C3C if counts.get("critical", 0) > 0 else 0xF39C12)
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
        {"name": "Files Reviewed", "value": str(len(report.get("reviewed_files", []))), "inline": True},
        {"name": "Reviewer", "value": f"{report.get('backend','?')} / {report.get('model_used','?')}", "inline": True},
    ]
    if report.get("summary"):
        fields.append({"name": "Summary", "value": report["summary"][:1024], "inline": False})

    critical = [i for i in report.get("issues", []) if i.get("severity") == "critical"]
    if critical:
        lines = []
        for i in critical[:5]:
            loc = i.get("file", "")
            if i.get("line"):
                loc += f":{i['line']}"
            lines.append(f"• `{loc}` — {i.get('issue', '')[:80]}")
        fields.append({
            "name": f"🔴 Critical Issues ({len(critical)})",
            "value": "\n".join(lines)[:1024],
            "inline": False,
        })

    payload = {"embeds": [{
        "title": f"{'✅' if passed else '❌'} Code Review — {q.upper()} ({score}/100)",
        "description": "Claude reviewed the AI-generated code before it was pushed to GitHub.",
        "color": color,
        "fields": fields,
        "timestamp": report.get("timestamp", datetime.utcnow().isoformat()) + "Z",
    }]}

    try:
        r = _requests.post(webhook_url, json=payload, timeout=10)
        r.raise_for_status()
        logger.info("✅ Discord review summary sent")
    except Exception as e:
        logger.warning(f"Failed to send Discord notification: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Review AI-generated Android code using the claude CLI "
            "(subscription) or Anthropic API (fallback)"
        )
    )
    parser.add_argument(
        "--project-dir", default=".",
        help="Root of the Android project to review (default: .)",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL}). "
             "E.g. claude-opus-4-6 for deeper review.",
    )
    parser.add_argument(
        "--api-key", default=os.getenv("ANTHROPIC_API_KEY"),
        help="Anthropic API key — only used if the claude CLI is not on PATH "
             "(or ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--output-json",
        help="Write full report to this JSON file",
    )
    parser.add_argument(
        "--pass-threshold", type=int, default=60,
        help="Minimum quality score (0–100) to exit 0. "
             "Critical issues always fail regardless. (default: 60)",
    )
    parser.add_argument(
        "--discord-webhook", default=os.getenv("DISCORD_WEBHOOK_URL"),
        help="Discord webhook URL for summary notification (optional)",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress the formatted console report",
    )

    args = parser.parse_args()

    reviewer = AndroidCodeReviewer(
        project_dir=args.project_dir,
        model=args.model,
        pass_threshold=args.pass_threshold,
        api_key=args.api_key,
    )

    try:
        report = reviewer.run()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Could not parse Claude's response as JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

    if not args.quiet:
        print_report(report)

    if args.output_json:
        out = Path(args.output_json)
        out.write_text(json.dumps(report, indent=2))
        logger.info(f"✅ Review report saved: {out}")

    if args.discord_webhook:
        send_discord_summary(report, args.discord_webhook)

    sys.exit(0 if report.get("passed") else 1)


if __name__ == "__main__":
    main()
