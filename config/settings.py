# ─────────────────────────────────────────────
# config/settings.py
# Central configuration for the Streaming QA Framework
# Change these values to test any streaming endpoint
# ─────────────────────────────────────────────

# The streaming URL you want to test.
# Using a public Big Buck Bunny HLS stream as a safe default.
STREAM_URL = "https://httpbin.org/stream/5"

# How many concurrent users to simulate in load tests
CONCURRENT_USERS = 10

# Total number of requests per load test run
TOTAL_REQUESTS = 50

# Thresholds — if results are worse than these, the test FAILS
MAX_ALLOWED_LATENCY_MS = 3000       # 3 seconds max per request
MIN_SUCCESS_RATE_PERCENT = 90       # At least 90% of requests must succeed
MAX_ALLOWED_ERROR_RATE_PERCENT = 10 # No more than 10% errors

# HTTP headers to mimic a real video player
STREAM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; StreamingQABot/1.0)",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

# Timeout per request in seconds
REQUEST_TIMEOUT = 10
