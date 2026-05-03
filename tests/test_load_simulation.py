# ─────────────────────────────────────────────
# tests/test_load_simulation.py
# Simulates concurrent users hitting the stream
# This is where "distributed systems" thinking lives
# Run with: pytest tests/test_load_simulation.py -v
# ─────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import concurrent.futures
import time
from config.settings import (
    STREAM_URL,
    CONCURRENT_USERS,
    TOTAL_REQUESTS,
    MAX_ALLOWED_LATENCY_MS,
    MIN_SUCCESS_RATE_PERCENT,
)
from utils.helpers import fetch_url, compute_summary, print_result


def run_load_test(url: str, total_requests: int, workers: int) -> list:
    """
    Fires `total_requests` HTTP requests across `workers` threads simultaneously.
    This simulates real concurrent user load on the stream.

    concurrent.futures.ThreadPoolExecutor is Python's built-in
    way to run many things at once without complex threading code.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all requests at once to simulate true concurrency
        futures = [executor.submit(fetch_url, url) for _ in range(total_requests)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print_result(result)
            results.append(result)
    return results


class TestLoadSimulation:
    """Simulates multiple concurrent users hitting the stream endpoint."""

    @pytest.fixture(scope="class")
    def load_results(self):
        """
        Runs the load test once and shares results across all tests in this class.
        This avoids hammering the server multiple times for each test.
        """
        print(f"\n🚀 Starting load test: {TOTAL_REQUESTS} requests, {CONCURRENT_USERS} concurrent users")
        print(f"   Target: {STREAM_URL}\n")

        start_time = time.time()
        results = run_load_test(STREAM_URL, TOTAL_REQUESTS, CONCURRENT_USERS)
        total_time = round(time.time() - start_time, 2)

        summary = compute_summary(results)
        summary["total_time_sec"] = total_time
        summary["throughput_rps"] = round(TOTAL_REQUESTS / total_time, 2)

        # Print a nice summary table
        print(f"\n{'─'*50}")
        print(f"  LOAD TEST SUMMARY")
        print(f"{'─'*50}")
        print(f"  Total requests   : {summary['total']}")
        print(f"  Passed           : {summary['passed']}")
        print(f"  Failed           : {summary['failed']}")
        print(f"  Success rate     : {summary['success_rate']}%")
        print(f"  Avg latency      : {summary['avg_latency_ms']}ms")
        print(f"  Max latency      : {summary['max_latency_ms']}ms")
        print(f"  Min latency      : {summary['min_latency_ms']}ms")
        print(f"  Total time       : {total_time}s")
        print(f"  Throughput       : {summary['throughput_rps']} req/sec")
        print(f"{'─'*50}\n")

        return {"results": results, "summary": summary}

    def test_success_rate_meets_threshold(self, load_results):
        """
        At least MIN_SUCCESS_RATE_PERCENT of all requests must succeed.
        Below this threshold means the server can't handle the load.
        """
        rate = load_results["summary"]["success_rate"]
        assert rate >= MIN_SUCCESS_RATE_PERCENT, (
            f"Success rate {rate}% is below the required {MIN_SUCCESS_RATE_PERCENT}%"
        )

    def test_average_latency_under_threshold(self, load_results):
        """
        Average latency across all users must stay under the allowed threshold.
        Spikes affect all concurrent viewers during a live event.
        """
        avg = load_results["summary"]["avg_latency_ms"]
        assert avg is not None, "Could not compute average latency — all requests failed."
        assert avg <= MAX_ALLOWED_LATENCY_MS, (
            f"Average latency {avg}ms exceeds threshold {MAX_ALLOWED_LATENCY_MS}ms"
        )

    def test_no_total_failure(self, load_results):
        """Sanity check — at least one request must have succeeded."""
        assert load_results["summary"]["passed"] > 0, (
            "Every single request failed. The endpoint may be down."
        )

    def test_throughput_is_acceptable(self, load_results):
        """
        System should handle at least 1 request/second.
        Very low throughput means the server is severely throttled.
        """
        rps = load_results["summary"]["throughput_rps"]
        assert rps >= 1.0, f"Throughput too low: {rps} req/sec"
