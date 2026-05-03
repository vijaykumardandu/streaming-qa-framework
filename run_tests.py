# ─────────────────────────────────────────────
# run_tests.py
# One-click entry point to run all tests and generate an HTML report
# Usage: python run_tests.py
# ─────────────────────────────────────────────

import subprocess
import sys
import os
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

def main():
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(report_dir, f"report_{timestamp}.html")

    print(f"\n{Fore.CYAN}{'═'*55}")
    print(f"  🎬  STREAMING QA FRAMEWORK")
    print(f"  Running all tests — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*55}{Style.RESET_ALL}\n")

    # Build the pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",                          # verbose output
        "--tb=short",                  # shorter tracebacks
        f"--html={report_path}",       # save HTML report
        "--self-contained-html",       # single file report (no extra folders)
        "--no-header",
    ]

    result = subprocess.run(cmd)

    print(f"\n{Fore.CYAN}{'─'*55}{Style.RESET_ALL}")
    if result.returncode == 0:
        print(f"{Fore.GREEN}  ✅  All tests passed!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}  ❌  Some tests failed. Check above for details.{Style.RESET_ALL}")

    print(f"  📄  HTML report saved: {report_path}")
    print(f"{Fore.CYAN}{'─'*55}{Style.RESET_ALL}\n")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
