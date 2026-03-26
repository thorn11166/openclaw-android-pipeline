#!/usr/bin/env python3
"""
Claude Code Reviewer for Android Projects — Prompt Builder & Response Parser

This script has two modes that bracket a sessions_spawn() call by Zoidberg:

  MODE 1 — Build prompt (--output-prompt):
    Collect all .kt/.java/.xml/.kts source files from the project directory
    and write a structured review prompt to a file. Zoidberg then passes
    that prompt to sessions_spawn(model="anthropic/claude-opus-4-6") and
    saves the response to a file.

  MODE 2 — Parse response (--response-file):
    Read the raw JSON response from the sub-agent, normalise it into a
    standard report, write it to --output-json, print a formatted summary,
    and exit 0 (passed) or 1 (critical issues / low score).

Full Phase 2.5 flow (orchestrated by Zoidberg via SKILL.md):

    1. python code-reviewer.py --project-dir . --output-prompt .review-prompt.txt
    2. [Zoidberg] sessions_spawn(model="anthropic/claude-sonnet-4-6", prompt=<file>)
    3. [Zoidberg] save sub-agent response to .review-response.txt
    4. python code-reviewer.py --response-file .review-response.txt \\
           --output-json .code-review-report.json
    5. [Zoidberg] if exit 1: send prompt_for_model to DeepSeek for revision

Usage:
    # Step 1 — build prompt:
    python code-reviewer.py --project-dir /path/to/project \\
        --output-prompt .review-prompt.txt

    # Step 4 — parse response:
    python code-reviewer.py --response-file .review-response.txt \\
        --output-json .code-review-report.json \\
        --pass-threshold 60
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# requests is only needed for Discord notifications
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

SKIP_DIRS = {
    "build", ".gradle", ".idea", "__pycache__", "node_modules",
    "intermediates", "generated", "outputs", ".git",
}
SKIP_FILES = {"gradlew", "gradlew.bat"}
REVIEW_EXTENSIONS = {".kt", ".java", ".xml", ".kts"}
MAX_FILE_BYTES = 40_000


# ---------------------------------------------------------------------------
# MODE 1 — Prompt builder
# ---------------------------------------------------------------------------

def _should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.name in SKIP_FILES:
        return True
    if path.stat().st_size > MAX_FILE_BYTES:
        logger.warning(f"Skipping large file ({path.stat().st_size} bytes): {path.name}")
        return True
    return False


def collect_source_files(project_dir: Path) -> Dict[str, str]:
    files: Dict[str, str] = {}
    for ext in REVIEW_EXTENSIONS:
        for fpath in sorted(project_dir.rglob(f"*{ext}")):
            rel = fpath.relative_to(project_dir)
            if _should_skip(fpath):
                continue
            try:
                files[str(rel)] = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Could not read {rel}: {e}")
    logger.info(f"Collected {len(files)} source file(s) for review")
    return files


def build_prompt(source_files: Dict[str, str]) -> str:
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


def mode_build_prompt(project_dir: str, output_prompt: str) -> None:
    pdir = Path(project_dir).resolve()
    source_files = collect_source_files(pdir)

    if not source_files:
        logger.error("No reviewable source files found — aborting")
        sys.exit(1)

    prompt = build_prompt(source_files)
    out = Path(output_prompt)
    out.write_text(prompt, encoding="utf-8")

    logger.info(f"✅ Review prompt written to: {out}")
    logger.info(f"   Files included: {', '.join(source_files.keys())}")
    logger.info("")
    logger.info("Next step — in Zoidberg:")
    logger.info(f'  sessions_spawn(model="anthropic/claude-sonnet-4-6", prompt_file="{out}")')
    logger.info("  Save the sub-agent response to .review-response.txt")
    logger.info("  Then run: python code-reviewer.py --response-file .review-response.txt "
                "--output-json .code-review-report.json")


# ---------------------------------------------------------------------------
# MODE 2 — Response parser
# ---------------------------------------------------------------------------

def parse_json_response(text: str) -> Dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def mode_parse_response(
    response_file: str,
    output_json: Optional[str],
    pass_threshold: int,
    discord_webhook: Optional[str],
    quiet: bool,
    model_used: str,
    project_dir: str,
) -> None:
    raw = Path(response_file).read_text(encoding="utf-8")

    try:
        review = parse_json_response(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Sub-agent response is not valid JSON: {e}")
        logger.error(f"Raw response (first 500 chars): {raw[:500]}")
        sys.exit(1)

    issues = review.get("issues", [])
    counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in issues:
        sev = issue.get("severity", "low")
        if sev in counts:
            counts[sev] += 1

    quality_score = int(review.get("quality_score", 0))
    passed = quality_score >= pass_threshold and counts["critical"] == 0

    report = {
        "timestamp": datetime.now().isoformat(),
        "model_used": model_used,
        "project_dir": str(Path(project_dir).resolve()),
        "overall_quality": review.get("overall_quality", "unknown"),
        "quality_score": quality_score,
        "summary": review.get("summary", ""),
        "issues": issues,
        "issue_counts": counts,
        "prompt_for_model": review.get("prompt_for_model", ""),
        "passed": passed,
    }

    if not quiet:
        print_report(report)

    if output_json:
        out = Path(output_json)
        out.write_text(json.dumps(report, indent=2))
        logger.info(f"✅ Review report saved: {out}")

    if discord_webhook:
        send_discord_summary(report, discord_webhook)

    sys.exit(0 if passed else 1)


# ---------------------------------------------------------------------------
# Reporting
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
    print(f"  Model   : {report.get('model_used', 'unknown')}")
    print(f"  Summary : {report.get('summary', '')}")
    print(f"  Issues  : 🔴 {counts.get('critical', 0)} critical  "
          f"🟠 {counts.get('high', 0)} high  "
          f"🟡 {counts.get('medium', 0)} medium  "
          f"🔵 {counts.get('low', 0)} low")
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
        print("  PROMPT FOR CODE-GENERATING MODEL (DeepSeek)")
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
        {"name": "Reviewer Model", "value": report.get("model_used", "unknown"), "inline": True},
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
            "Phase 2.5 code review helper. Run in two steps:\n"
            "  1. --output-prompt  : collect files and write review prompt\n"
            "  2. --response-file  : parse sub-agent response into report\n"
            "Between steps, Zoidberg calls sessions_spawn() with the prompt."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mode 1
    parser.add_argument(
        "--project-dir", default=".",
        help="Root of the Android project (used in step 1)",
    )
    parser.add_argument(
        "--output-prompt",
        help="(Step 1) Write the review prompt to this file",
    )

    # Mode 2
    parser.add_argument(
        "--response-file",
        help="(Step 2) Path to the raw JSON response from the sub-agent",
    )
    parser.add_argument(
        "--model-used", default="anthropic/claude-sonnet-4-6",
        help="Model that performed the review (recorded in report, default: anthropic/claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--output-json",
        help="(Step 2) Write the parsed report to this JSON file",
    )
    parser.add_argument(
        "--pass-threshold", type=int, default=60,
        help="(Step 2) Minimum quality score to exit 0. Critical issues always fail. (default: 60)",
    )
    parser.add_argument(
        "--discord-webhook",
        help="(Step 2) Discord webhook URL for summary notification",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="(Step 2) Suppress formatted console report",
    )

    args = parser.parse_args()

    if args.output_prompt:
        mode_build_prompt(args.project_dir, args.output_prompt)
    elif args.response_file:
        mode_parse_response(
            response_file=args.response_file,
            output_json=args.output_json,
            pass_threshold=args.pass_threshold,
            discord_webhook=args.discord_webhook,
            quiet=args.quiet,
            model_used=args.model_used,
            project_dir=args.project_dir,
        )
    else:
        parser.error("Specify either --output-prompt (step 1) or --response-file (step 2)")


if __name__ == "__main__":
    main()
