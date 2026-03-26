#!/usr/bin/env python3
"""
Android Build Error Recovery & Retry Orchestrator

Main loop that monitors builds, detects errors, applies fixes, and retries.
Integrates error-parser.py and auto-fix.py for full error recovery pipeline.

Usage:
    python error-recovery.py \
        --repo owner/repo \
        --github-token $GITHUB_TOKEN \
        --discord-webhook $DISCORD_WEBHOOK_URL \
        --project-dir . \
        --max-retries 3
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List

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


class RecoveryState(Enum):
    """States in error recovery cycle."""
    MONITORING = "monitoring"
    ERROR_DETECTED = "error_detected"
    PARSING_ERRORS = "parsing_errors"
    GENERATING_FIXES = "generating_fixes"
    APPLYING_FIXES = "applying_fixes"
    COMMITTING = "committing"
    PUSHING = "pushing"
    RETRIGGERING_BUILD = "retriggering_build"
    ESCALATING = "escalating"
    COMPLETE_SUCCESS = "complete_success"
    COMPLETE_FAILURE = "complete_failure"


@dataclass
class RetryAttempt:
    """Record of a single retry attempt."""
    attempt_number: int
    error_type: str
    error_count: int
    fixes_applied: int
    success: bool
    timestamp: str
    run_id: Optional[int] = None
    error_summary: str = ""


class ErrorRecoveryOrchestrator:
    """Coordinates error detection, fixing, and retry logic."""

    def __init__(
        self,
        repo: str,
        github_token: str,
        discord_webhook: str,
        project_dir: str = ".",
        max_retries: int = 3,
    ):
        """
        Initialize orchestrator.

        Args:
            repo: Repository (owner/repo)
            github_token: GitHub personal access token
            discord_webhook: Discord webhook URL
            project_dir: Android project directory
            max_retries: Maximum retry attempts per error type
        """
        self.repo = repo
        self.github_token = github_token
        self.discord_webhook = discord_webhook
        self.project_dir = Path(project_dir)
        self.max_retries = max_retries
        self.retry_history: List[RetryAttempt] = []
        self.state = RecoveryState.MONITORING
        self.error_recovery_log = self.project_dir / ".error-recovery.log"

    def run_full_recovery_cycle(
        self,
        run_id: int,
        build_monitor_script: str = "scripts/build-monitor.py",
        error_parser_script: str = "scripts/error-parser.py",
        auto_fix_script: str = "scripts/auto-fix.py",
    ) -> bool:
        """
        Execute full error recovery cycle: monitor → detect → fix → retry.

        Args:
            run_id: GitHub Actions run ID to monitor
            build_monitor_script: Path to build-monitor.py
            error_parser_script: Path to error-parser.py
            auto_fix_script: Path to auto-fix.py

        Returns:
            True if build succeeds, False if max retries exceeded
        """
        self._log(f"🚀 Starting error recovery cycle for run #{run_id}")
        self._notify_discord(
            "milestone",
            "Build Monitoring Started",
            f"Monitoring run #{run_id}",
        )

        # Phase 1: Monitor build
        self._log(f"📊 Phase 1: Monitoring build...")
        self.state = RecoveryState.MONITORING
        success = self._run_build_monitor(run_id, build_monitor_script)

        if success:
            self.state = RecoveryState.COMPLETE_SUCCESS
            self._log("✅ BUILD SUCCEEDED on first attempt!")
            self._notify_discord(
                "status",
                "success",
                run_id,
                f"Build succeeded on first try!",
            )
            return True

        # Phase 2: Error detection and recovery loop
        self._log("❌ Build failed, starting error recovery loop...")
        self.state = RecoveryState.ERROR_DETECTED

        for attempt in range(1, self.max_retries + 1):
            self._log(f"\n{'=' * 60}")
            self._log(f"RECOVERY ATTEMPT {attempt}/{self.max_retries}")
            self._log(f"{'=' * 60}")

            # Get logs from failed run
            logs_file = self.project_dir / f"build-logs/run-{run_id}.log"
            if not logs_file.exists():
                self._log(f"⚠️  Logs file not found, skipping recovery")
                break

            # Parse errors
            self.state = RecoveryState.PARSING_ERRORS
            error_json = self._parse_errors(logs_file, error_parser_script)
            if not error_json:
                self._log("⚠️  Failed to parse errors")
                break

            error_report = json.loads(error_json.read_text())
            error_count = error_report.get("total_errors", 0)
            errors_by_type = error_report.get("errors_by_type", {})

            self._log(f"🔍 Found {error_count} errors:")
            for err_type, count in errors_by_type.items():
                self._log(f"   • {err_type}: {count}")

            # Generate fixes
            self.state = RecoveryState.GENERATING_FIXES
            fixes_json = self._generate_fixes(error_json, auto_fix_script)
            if not fixes_json:
                self._log("⚠️  Failed to generate fixes")
                self.state = RecoveryState.ESCALATING
                break

            fixes_report = json.loads(fixes_json.read_text())
            fixes_count = fixes_report.get("total_suggestions", 0)

            self._log(f"💡 Generated {fixes_count} fix suggestions")

            # Apply fixes
            self.state = RecoveryState.APPLYING_FIXES
            fixes_applied = self._apply_fixes(error_json, auto_fix_script)
            self._log(f"🔧 Applied {fixes_applied} fix(es)")

            # Commit and push
            self.state = RecoveryState.COMMITTING
            if not self._commit_changes(attempt):
                self._log("⚠️  Failed to commit changes")
                break

            self.state = RecoveryState.PUSHING
            if not self._push_changes():
                self._log("⚠️  Failed to push changes")
                break

            # Retrigger build
            self.state = RecoveryState.RETRIGGERING_BUILD
            new_run_id = self._retrigger_build()
            if not new_run_id:
                self._log("⚠️  Failed to retrigger build")
                break

            run_id = new_run_id
            self._log(f"🔄 New build triggered: run #{run_id}")

            # Monitor new build
            self.state = RecoveryState.MONITORING
            time.sleep(5)  # Give GitHub a moment to register the build
            success = self._run_build_monitor(run_id, build_monitor_script)

            # Record attempt
            first_error_type = list(errors_by_type.keys())[0] if errors_by_type else "unknown"
            self.retry_history.append(
                RetryAttempt(
                    attempt_number=attempt,
                    error_type=first_error_type,
                    error_count=error_count,
                    fixes_applied=fixes_applied,
                    success=success,
                    timestamp=datetime.now().isoformat(),
                    run_id=run_id,
                    error_summary=f"{error_count} errors of {len(errors_by_type)} types",
                )
            )

            if success:
                self.state = RecoveryState.COMPLETE_SUCCESS
                self._log(f"✅ BUILD SUCCEEDED after {attempt} attempt(s)!")
                self._notify_discord(
                    "status",
                    "success",
                    run_id,
                    f"Build succeeded after {attempt} retry attempt(s)",
                    retry=attempt,
                )
                self._save_recovery_log()
                return True

        # Max retries exceeded
        self.state = RecoveryState.COMPLETE_FAILURE
        self._log(f"\n❌ Max retries ({self.max_retries}) exceeded")
        self._log("⛔ ESCALATING TO DISCORD")

        # Escalate to Discord
        logs_file = self.project_dir / f"build-logs/run-{run_id}.log"
        if logs_file.exists():
            self._escalate_to_discord(run_id, logs_file)

        self._save_recovery_log()
        return False

    def _run_build_monitor(self, run_id: int, script: str) -> bool:
        """Run build monitor script."""
        try:
            result = subprocess.run(
                [
                    "python",
                    script,
                    "--repo",
                    self.repo,
                    "--run-id",
                    str(run_id),
                    "--github-token",
                    self.github_token,
                    "--poll-interval",
                    "20",
                ],
                capture_output=True,
                text=True,
                timeout=2000,  # 30+ minutes
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self._log("⚠️  Build monitor timed out")
            return False
        except Exception as e:
            self._log(f"❌ Build monitor error: {e}")
            return False

    def _parse_errors(self, log_file: Path, script: str) -> Optional[Path]:
        """Run error parser and return JSON output file."""
        output_file = self.project_dir / f".error-report-{int(time.time())}.json"

        try:
            result = subprocess.run(
                [
                    "python",
                    script,
                    "--log-file",
                    str(log_file),
                    "--output-format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self._log(f"⚠️  Error parser failed: {result.stderr}")
                return None

            # Parser returns JSON on stdout
            error_report = json.loads(result.stdout)
            output_file.write_text(json.dumps(error_report, indent=2))
            return output_file

        except json.JSONDecodeError as e:
            self._log(f"❌ JSON parse error: {e}")
            return None
        except Exception as e:
            self._log(f"❌ Error parsing errors: {e}")
            return None

    def _generate_fixes(self, error_json: Path, script: str) -> Optional[Path]:
        """Run auto-fix script to generate suggestions."""
        output_file = self.project_dir / f".fixes-report-{int(time.time())}.json"

        try:
            result = subprocess.run(
                [
                    "python",
                    script,
                    "--error-json",
                    str(error_json),
                    "--project-dir",
                    str(self.project_dir),
                    "--output-json",
                    str(output_file),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if not output_file.exists():
                self._log(f"⚠️  Fixes output file not created")
                return None

            return output_file

        except Exception as e:
            self._log(f"❌ Error generating fixes: {e}")
            return None

    def _apply_fixes(self, error_json: Path, script: str) -> int:
        """Apply fixes to project files."""
        try:
            result = subprocess.run(
                [
                    "python",
                    script,
                    "--error-json",
                    str(error_json),
                    "--project-dir",
                    str(self.project_dir),
                    "--apply",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Count "✅" in output
            count = result.stderr.count("✅") + result.stdout.count("✅")
            return count

        except Exception as e:
            self._log(f"❌ Error applying fixes: {e}")
            return 0

    def _commit_changes(self, attempt: int) -> bool:
        """Commit fixed files to git."""
        try:
            # Stage changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=30,
            )

            # Commit
            message = f"Auto-fix: Error recovery attempt #{attempt} [skip ci]"
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # No changes to commit
                self._log("ℹ️  No changes to commit")
                return True

            self._log(f"✅ Committed: '{message}'")
            return True

        except Exception as e:
            self._log(f"❌ Git commit error: {e}")
            return False

    def _push_changes(self) -> bool:
        """Push changes to GitHub."""
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                self._log("✅ Changes pushed to GitHub")
                return True
            else:
                self._log(f"⚠️  Git push failed: {result.stderr[:200]}")
                return False

        except Exception as e:
            self._log(f"❌ Git push error: {e}")
            return False

    def _retrigger_build(self) -> Optional[int]:
        """Trigger a new GitHub Actions build by pushing empty commit."""
        try:
            # Push triggers workflow (if configured)
            result = subprocess.run(
                ["git", "push"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Try to get new run ID from API
                # This is a best-effort; actual run ID will be discovered by monitoring
                time.sleep(3)
                run_id = self._get_latest_run_id()
                if run_id:
                    return run_id
                # Fallback: return None and let caller know to poll
                return None

            return None

        except Exception as e:
            self._log(f"❌ Retrigger error: {e}")
            return None

    def _get_latest_run_id(self) -> Optional[int]:
        """Get latest run ID for repo."""
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"https://api.github.com/repos/{self.repo}/actions/runs?per_page=1"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("workflow_runs"):
                return data["workflow_runs"][0]["id"]

        except Exception as e:
            self._log(f"⚠️  Failed to get latest run ID: {e}")

        return None

    def _escalate_to_discord(self, run_id: int, log_file: Path) -> None:
        """Send escalation alert to Discord."""
        try:
            log_content = log_file.read_text()[-1000:]  # Last 1000 chars

            # Build retry summary
            summary_lines = [f"Retry Attempts: {len(self.retry_history)}/{self.max_retries}"]
            for attempt in self.retry_history:
                status = "✅" if attempt.success else "❌"
                summary_lines.append(
                    f"  {status} Attempt {attempt.attempt_number}: "
                    f"{attempt.error_type} ({attempt.error_count} errors, "
                    f"{attempt.fixes_applied} fixes)"
                )

            summary = "\n".join(summary_lines)

            payload = {
                "embeds": [
                    {
                        "title": "🔴 Build Recovery Failed - Escalation",
                        "description": f"Run #{run_id} in [{self.repo}]"
                        f"(https://github.com/{self.repo}/actions/runs/{run_id})",
                        "color": 0xE74C3C,
                        "fields": [
                            {
                                "name": "Recovery Summary",
                                "value": f"```\n{summary}\n```",
                                "inline": False,
                            },
                            {
                                "name": "Final Error Log",
                                "value": f"```\n{log_content}\n```",
                                "inline": False,
                            },
                            {
                                "name": "Next Steps",
                                "value": (
                                    "1. Review logs above\n"
                                    "2. Debug locally\n"
                                    "3. Commit and push fixes\n"
                                    "4. Re-run build"
                                ),
                                "inline": False,
                            },
                        ],
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                ]
            }

            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            self._log("✅ Escalation alert sent to Discord")

        except Exception as e:
            self._log(f"⚠️  Failed to send escalation: {e}")

    def _notify_discord(
        self,
        notify_type: str,
        *args,
        **kwargs,
    ) -> None:
        """Send generic Discord notification."""
        try:
            if notify_type == "milestone":
                title = args[0] if args else "Milestone"
                desc = args[1] if len(args) > 1 else ""
                embed = {
                    "title": f"🚀 {title}",
                    "description": desc,
                    "color": 0x3498DB,
                }
            elif notify_type == "status":
                status = args[0]
                run_id = args[1] if len(args) > 1 else 0
                msg = args[2] if len(args) > 2 else ""
                retry = kwargs.get("retry", 0)

                emoji = "✅" if status == "success" else "❌"
                embed = {
                    "title": f"{emoji} Build {status.upper()}",
                    "description": f"Run #{run_id}\n{msg}",
                    "color": 0x2ECC71 if status == "success" else 0xE74C3C,
                }
                if retry > 0:
                    embed["fields"] = [
                        {"name": "Retry Attempt", "value": str(retry)}
                    ]
            else:
                return

            payload = {
                "embeds": [embed],
            }

            requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10,
            )

        except Exception as e:
            logger.warning(f"Failed to send Discord notification: {e}")

    def _log(self, message: str) -> None:
        """Log message."""
        logger.info(message)
        try:
            with open(self.error_recovery_log, "a") as f:
                f.write(f"{datetime.now().isoformat()} {message}\n")
        except Exception as e:
            logger.warning(f"Failed to write to log file: {e}")

    def _save_recovery_log(self) -> None:
        """Save recovery history to JSON."""
        history_file = self.project_dir / ".error-recovery-history.json"

        history = {
            "final_state": self.state.value,
            "total_attempts": len(self.retry_history),
            "max_retries": self.max_retries,
            "success": self.state == RecoveryState.COMPLETE_SUCCESS,
            "timestamp": datetime.now().isoformat(),
            "attempts": [asdict(a) for a in self.retry_history],
        }

        history_file.write_text(json.dumps(history, indent=2))
        self._log(f"✅ Recovery history saved: {history_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Android build error recovery and retry orchestrator"
    )
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument(
        "--github-token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub token (or GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--discord-webhook",
        default=os.getenv("DISCORD_WEBHOOK_URL"),
        help="Discord webhook URL (or DISCORD_WEBHOOK_URL env var)",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Android project directory",
    )
    parser.add_argument(
        "--run-id",
        type=int,
        required=True,
        help="GitHub Actions run ID to monitor",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts per error type",
    )

    args = parser.parse_args()

    if not args.github_token:
        print("ERROR: GitHub token required")
        sys.exit(1)

    if not args.discord_webhook:
        print("WARNING: Discord webhook not provided (escalation disabled)")

    orchestrator = ErrorRecoveryOrchestrator(
        repo=args.repo,
        github_token=args.github_token,
        discord_webhook=args.discord_webhook or "",
        project_dir=args.project_dir,
        max_retries=args.max_retries,
    )

    success = orchestrator.run_full_recovery_cycle(args.run_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
