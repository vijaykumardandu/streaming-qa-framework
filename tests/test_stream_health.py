# ─────────────────────────────────────────────
# tests/test_stream_health.py
# Basic health checks for the streaming endpoint
# Run with: pytest tests/test_stream_health.py -v
# ─────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import requests
from config.settings import (
    STREAM_URL,
    MAX_ALLOWED_LATENCY_MS,
    STREAM_HEADERS,
    REQUEST_TIMEOUT,
)
from utils.helpers import fetch_url


class TestStreamAvailability:
    """Tests that check if the stream is reachable and responsive."""

    def test_stream_is_reachable(self):
        """The most basic check — can we even connect to the stream?"""
        result = fetch_url(STREAM_URL)
        assert result["error"] is None, (
            f"Could not reach stream. Error: {result['error']}"
        )

    def test_stream_returns_200(self):
        """Stream endpoint must return HTTP 200 OK."""
        result = fetch_url(STREAM_URL)
        assert result["status_code"] == 200, (
            f"Expected 200, got {result['status_code']}. Error: {result['error']}"
        )

    def test_stream_latency_within_threshold(self):
        """
        Response must arrive within MAX_ALLOWED_LATENCY_MS milliseconds.
        A slow first response means users will see buffering.
        """
        result = fetch_url(STREAM_URL)
        assert result["latency_ms"] is not None, "Could not measure latency — request failed."
        assert result["latency_ms"] <= MAX_ALLOWED_LATENCY_MS, (
            f"Latency {result['latency_ms']}ms exceeds threshold of {MAX_ALLOWED_LATENCY_MS}ms"
        )

    def test_stream_returns_content(self):
        """
        Stream endpoint must return a non-empty body.
        An empty response usually means a misconfigured CDN edge node.
        """
        response = requests.get(STREAM_URL, headers=STREAM_HEADERS, timeout=REQUEST_TIMEOUT)
        assert len(response.content) > 0, "Stream returned an empty body."

    def test_stream_content_type(self):
        """
        For HLS streams, content-type should be application/x-mpegURL or similar.
        This catches CDN misconfigurations where the wrong MIME type is served.
        """
        response = requests.get(STREAM_URL, headers=STREAM_HEADERS, timeout=REQUEST_TIMEOUT)
        content_type = response.headers.get("Content-Type", "")
        # Accept common streaming MIME types
        valid_types = [
            "application/x-mpegurl",
            "application/vnd.apple.mpegurl",
            "video/mp4",
            "application/octet-stream",
            "text/plain",
            "application/json",  # for test endpoints like httpbin
        ]
        assert any(vt in content_type.lower() for vt in valid_types), (
            f"Unexpected content-type: '{content_type}'. "
            f"CDN may be misconfigured."
        )

    def test_no_redirect_loops(self):
        """
        Follows up to 5 redirects and ensures we're not stuck in a loop.
        Redirect loops are a common CDN/edge misconfiguration.
        """
        response = requests.get(
            STREAM_URL,
            headers=STREAM_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        # requests.Response.history contains the list of redirects
        assert len(response.history) < 5, (
            f"Too many redirects ({len(response.history)}). Possible redirect loop."
        )


class TestStreamConsistency:
    """Tests that check if repeated requests give consistent results."""

    def test_three_consecutive_requests_all_succeed(self):
        """
        Hits the stream 3 times in a row.
        Intermittent failures indicate flaky edge node behaviour.
        """
        failures = []
        for i in range(3):
            result = fetch_url(STREAM_URL)
            if not result["success"]:
                failures.append(f"Request {i+1}: {result['error']}")

        assert len(failures) == 0, (
            f"Inconsistent responses detected:\n" + "\n".join(failures)
        )

    def test_latency_is_stable(self):
        """
        Checks that latency doesn't vary wildly across 5 requests.
        High variance means an unstable edge node.
        """
        latencies = []
        for _ in range(5):
            result = fetch_url(STREAM_URL)
            if result["latency_ms"] is not None:
                latencies.append(result["latency_ms"])

        assert len(latencies) >= 3, "Not enough successful responses to measure stability."

        avg = sum(latencies) / len(latencies)
        max_allowed_variance = avg * 3  # max latency shouldn't be 3x the average

        assert max(latencies) <= max_allowed_variance, (
            f"Latency is unstable. Avg: {avg:.1f}ms, Max: {max(latencies):.1f}ms"
        )
