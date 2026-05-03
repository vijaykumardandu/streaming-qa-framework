# ─────────────────────────────────────────────
# utils/helpers.py
# Shared helper functions used across the framework
# ─────────────────────────────────────────────

import time
import requests
from colorama import Fore, Style, init
from config.settings import STREAM_HEADERS, REQUEST_TIMEOUT

init(autoreset=True)  # makes colorama reset color after each print


def fetch_url(url: str) -> dict:
    """
    Makes a single HTTP GET request and returns timing + status info.

    Returns a dict like:
    {
        "url": "https://...",
        "status_code": 200,
        "latency_ms": 312.5,
        "success": True,
        "error": None
    }
    """
    result = {
        "url": url,
        "status_code": None,
        "latency_ms": None,
        "success": False,
        "error": None,
    }

    try:
        start = time.perf_counter()
        response = requests.get(url, headers=STREAM_HEADERS, timeout=REQUEST_TIMEOUT)
        elapsed_ms = (time.perf_counter() - start) * 1000

        result["status_code"] = response.status_code
        result["latency_ms"] = round(elapsed_ms, 2)
        result["success"] = response.status_code == 200

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        result["error"] = "Request timed out"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection failed"
    except Exception as e:
        result["error"] = str(e)

    return result


def print_result(result: dict):
    """Prints a single request result with color coding."""
    status = "✓ PASS" if result["success"] else "✗ FAIL"
    color = Fore.GREEN if result["success"] else Fore.RED

    latency = f"{result['latency_ms']}ms" if result["latency_ms"] else "N/A"
    error = f" | Error: {result['error']}" if result["error"] else ""

    print(f"{color}{status}{Style.RESET_ALL} | {latency:>10} | {result['url'][:60]}{error}")


def compute_summary(results: list) -> dict:
    """
    Takes a list of result dicts and computes summary statistics.
    """
    total = len(results)
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]

    return {
        "total": total,
        "passed": len(successes),
        "failed": len(failures),
        "success_rate": round(len(successes) / total * 100, 1) if total else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "max_latency_ms": round(max(latencies), 2) if latencies else None,
        "min_latency_ms": round(min(latencies), 2) if latencies else None,
    }
