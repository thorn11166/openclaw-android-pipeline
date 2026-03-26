#!/usr/bin/env python3
"""
GitHub Actions Build Monitor for Android Projects

Polls GitHub Actions workflow runs and tracks build status in real-time.
Captures logs on completion and exports to file for error parsing.

Usage:
    python build-monitor.py --repo owner/repo --workflow build.yml --run-id 12345 --github-token $GITHUB_TOKEN
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)


class GitHubActionsMonitor:
    """Monitor GitHub Actions workflow runs."""

    def __init__(self, repo: str, github_token: str):
        """
        Initialize monitor.

        Args:
            repo: Repository in format 'owner/repo'
            github_token: GitHub personal access token
        """
        self.repo = repo
        self.token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github+json",
        }

    def get_run_status(self, run_id: int) -> Dict[str, Any]:
        """
        Get current status of a workflow run.

        Args:
            run_id: GitHub Actions run ID

        Returns:
            Dict with status, conclusion, etc.
        """
        url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_run_logs(self, run_id: int) -> str:
        """
        Download logs for a completed run.

        Args:
            run_id: GitHub Actions run ID

        Returns:
            Full log text
        """
        url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}/logs"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text

    def save_logs(self, run_id: int, logs: str) -> Path:
        """
        Save logs to local file.

        Args:
            run_id: GitHub Actions run ID
            logs: Log text to save

        Returns:
            Path to saved log file
        """
        log_dir = Path("build-logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"run-{run_id}.log"
        log_file.write_text(logs)
        return log_file

    def monitor(
        self, run_id: int, poll_interval: int = 20, max_wait: int = 1800
    ) -> bool:
        """
        Monitor a run until completion.

        Args:
            run_id: GitHub Actions run ID
            poll_interval: Seconds between status checks (default 20)
            max_wait: Maximum seconds to wait before timing out (default 30 min)

        Returns:
            True if build succeeded, False if failed or timed out
        """
        start_time = time.time()
        last_status = None

        print(f"📊 Monitoring run #{run_id}...")
        print(f"⏱️  Poll interval: {poll_interval}s | Max wait: {max_wait}s\n")

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait:
                print(f"\n❌ TIMEOUT: Build exceeded {max_wait}s limit")
                return False

            try:
                data = self.get_run_status(run_id)
                status = data.get("status")
                conclusion = data.get("conclusion")
                name = data.get("name", "Unknown")
                html_url = data.get("html_url", "")

                # Print status if changed
                if status != last_status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Status: {status}")
                    last_status = status

                # Check if completed
                if status == "completed":
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    elapsed_min = elapsed / 60

                    print(f"\n{'=' * 60}")
                    print(f"[{timestamp}] Build completed in {elapsed_min:.1f}m")
                    print(f"{'=' * 60}")

                    # Fetch and save logs
                    print("📥 Downloading logs...")
                    logs = self.get_run_logs(run_id)
                    log_file = self.save_logs(run_id, logs)
                    print(f"✅ Logs saved: {log_file}")

                    # Print result
                    if conclusion == "success":
                        print(
                            f"\n✅ BUILD SUCCEEDED"
                        )
                        print(f"View details: {html_url}\n")
                        return True
                    else:
                        print(
                            f"\n❌ BUILD FAILED (conclusion: {conclusion})"
                        )
                        print(f"View details: {html_url}")
                        print(f"Log file: {log_file}\n")
                        return False

                # Still running, print progress
                print(".", end="", flush=True)

            except requests.exceptions.RequestException as e:
                print(f"\n⚠️  API error: {e}")
                print(f"Retrying in {poll_interval}s...\n")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                return False

            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor GitHub Actions Android builds"
    )
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument(
        "--workflow", default="build.yml", help="Workflow filename (default: build.yml)"
    )
    parser.add_argument("--run-id", type=int, required=True, help="Run ID to monitor")
    parser.add_argument(
        "--github-token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub token (or use GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--poll-interval", type=int, default=20, help="Poll interval in seconds"
    )
    parser.add_argument(
        "--max-wait", type=int, default=1800, help="Max wait time in seconds"
    )

    args = parser.parse_args()

    if not args.github_token:
        print("ERROR: GitHub token required. Set GITHUB_TOKEN env var or use --github-token")
        sys.exit(1)

    monitor = GitHubActionsMonitor(args.repo, args.github_token)

    try:
        success = monitor.monitor(args.run_id, args.poll_interval, args.max_wait)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
