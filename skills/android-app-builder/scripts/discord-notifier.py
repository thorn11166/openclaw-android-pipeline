#!/usr/bin/env python3
"""
Discord Build Notifier

Posts Android build status updates to Discord webhook as formatted embeds.
Tracks build history, errors, and retry attempts.

Usage:
    python discord-notifier.py --webhook-url $DISCORD_WEBHOOK_URL --status success --repo owner/repo --run-id 12345
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)


class DiscordNotifier:
    """Send build status notifications to Discord."""

    def __init__(self, webhook_url: str):
        """
        Initialize notifier with webhook URL.

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url

    def send_build_status(
        self,
        repo: str,
        run_id: int,
        status: str,
        run_url: str,
        elapsed_minutes: Optional[float] = None,
        error_summary: Optional[str] = None,
        retry_count: int = 0,
    ) -> bool:
        """
        Send build status embed to Discord.

        Args:
            repo: Repository name (owner/repo)
            run_id: GitHub Actions run ID
            status: 'success' or 'failure'
            run_url: URL to GitHub Actions run
            elapsed_minutes: Build duration in minutes
            error_summary: Error details if failed
            retry_count: Number of retries

        Returns:
            True if successful, False otherwise
        """
        # Color code: green for success, red for failure
        color = 0x2ECC71 if status == "success" else 0xE74C3C
        status_emoji = "✅" if status == "success" else "❌"

        title = f"{status_emoji} Android Build {status.upper()}"

        # Build embed fields
        fields = [
            {"name": "Repository", "value": f"[{repo}](https://github.com/{repo})", "inline": True},
            {"name": "Build #", "value": str(run_id), "inline": True},
        ]

        if elapsed_minutes:
            fields.append(
                {
                    "name": "Duration",
                    "value": f"{elapsed_minutes:.1f}m",
                    "inline": True,
                }
            )

        if retry_count > 0:
            fields.append(
                {
                    "name": "Retry #",
                    "value": str(retry_count),
                    "inline": True,
                }
            )

        if error_summary:
            # Truncate error summary to 1024 chars (Discord limit)
            truncated = error_summary[:1024]
            fields.append(
                {
                    "name": "Error Summary",
                    "value": f"```\n{truncated}\n```",
                    "inline": False,
                }
            )

        # Build embed
        embed = {
            "title": title,
            "description": f"Build run #{run_id}",
            "color": color,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "fields": fields,
            "url": run_url,
        }

        # Send to Discord
        payload = {"embeds": [embed]}

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            print(f"✅ Discord notification sent (status: {response.status_code})")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send Discord notification: {e}")
            return False

    def send_milestone(
        self,
        project_name: str,
        milestone: str,
        description: str = "",
    ) -> bool:
        """
        Send a milestone message (e.g., "Repo created", "Code generated").

        Args:
            project_name: App/project name
            milestone: Milestone text (e.g., "Repository Created")
            description: Optional details

        Returns:
            True if successful, False otherwise
        """
        embed = {
            "title": f"🚀 {milestone}",
            "description": f"**{project_name}**\n\n{description}" if description else project_name,
            "color": 0x3498DB,  # Blue
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        payload = {"embeds": [embed]}

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            print(f"✅ Milestone notification sent")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send milestone notification: {e}")
            return False

    def send_error_escalation(
        self,
        repo: str,
        run_id: int,
        error_log: str,
        max_retries_exceeded: bool = False,
    ) -> bool:
        """
        Send error escalation alert to Discord.

        Args:
            repo: Repository name
            run_id: GitHub Actions run ID
            error_log: Full error log
            max_retries_exceeded: If max retries were exceeded

        Returns:
            True if successful, False otherwise
        """
        # Truncate log to 1024 chars
        truncated_log = error_log[:1024]
        if len(error_log) > 1024:
            truncated_log += "\n... (truncated)"

        title = "⚠️ Build Escalation Alert"
        if max_retries_exceeded:
            title = "🔴 Max Retries Exceeded"

        embed = {
            "title": title,
            "description": f"Build #{run_id} in [{repo}](https://github.com/{repo})",
            "color": 0xE74C3C,  # Red
            "fields": [
                {
                    "name": "Error Log",
                    "value": f"```\n{truncated_log}\n```",
                    "inline": False,
                },
                {
                    "name": "Next Steps",
                    "value": "Review logs and debug locally, then push fixes to trigger new build",
                    "inline": False,
                },
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        payload = {"embeds": [embed]}

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            print(f"✅ Escalation alert sent")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send escalation alert: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Send Android build notifications to Discord")
    parser.add_argument(
        "--webhook-url",
        default=os.getenv("DISCORD_WEBHOOK_URL"),
        help="Discord webhook URL (or DISCORD_WEBHOOK_URL env var)",
    )
    parser.add_argument(
        "--status",
        choices=["success", "failure"],
        help="Build status",
    )
    parser.add_argument("--repo", help="Repository (owner/repo)")
    parser.add_argument("--run-id", type=int, help="GitHub Actions run ID")
    parser.add_argument("--run-url", help="URL to GitHub Actions run")
    parser.add_argument("--elapsed-minutes", type=float, help="Build duration in minutes")
    parser.add_argument("--error-summary", help="Error summary if failed")
    parser.add_argument("--retry-count", type=int, default=0, help="Retry attempt number")
    parser.add_argument("--milestone", help="Milestone message (alternative to --status)")
    parser.add_argument("--project-name", default="Project", help="Project name for milestone notifications")
    parser.add_argument(
        "--milestone-description", help="Milestone description"
    )
    parser.add_argument(
        "--escalation",
        action="store_true",
        help="Send escalation alert instead",
    )
    parser.add_argument("--error-log", help="Full error log for escalation")

    args = parser.parse_args()

    if not args.webhook_url:
        print("ERROR: Discord webhook URL required. Set DISCORD_WEBHOOK_URL or use --webhook-url")
        sys.exit(1)

    notifier = DiscordNotifier(args.webhook_url)

    try:
        if args.escalation:
            if not args.repo or not args.run_id or not args.error_log:
                print("ERROR: --escalation requires --repo, --run-id, and --error-log")
                sys.exit(1)
            success = notifier.send_error_escalation(
                args.repo,
                args.run_id,
                args.error_log,
                max_retries_exceeded=True,
            )
        elif args.milestone:
            success = notifier.send_milestone(
                args.project_name,
                args.milestone,
                args.milestone_description or "",
            )
        else:
            if not args.status or not args.repo or not args.run_id:
                print("ERROR: --status, --repo, and --run-id are required")
                sys.exit(1)

            run_url = args.run_url or f"https://github.com/{args.repo}/actions/runs/{args.run_id}"

            success = notifier.send_build_status(
                args.repo,
                args.run_id,
                args.status,
                run_url,
                args.elapsed_minutes,
                args.error_summary,
                args.retry_count,
            )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
