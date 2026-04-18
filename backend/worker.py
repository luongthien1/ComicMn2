"""
Background Worker — chạy độc lập với FastAPI server.

Liên tục quét bảng `tasks` tìm các task có status='pending' và chạy chúng.
Cũng kiểm tra task đang 'running' có bị cancel không.

Khởi động:
    venv\\Scripts\\python.exe -m backend.worker

Hoặc dùng script:
    venv\\Scripts\\python.exe backend/worker.py
"""

import os
import sys
import time

from lib.logger import logger

from backend.core.config import MAX_CONCURRENT, POLL_INTERVAL, TASK_TIMEOUT

# Ensure project root is in path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()
_running = True


def _handle_signal(sig, frame):
    global _running
    logger.info(f"Received signal {sig}, shutting down worker...")
    _running = False


def _check_cancelled_and_timed_out():
    """
    Check running tasks:
    1. If status was set to 'cancelled' externally → send cancel signal
    2. If running longer than TASK_TIMEOUT → auto-cancel
    """
    pass


def _scan_and_run():
    """One scan cycle: check cancellations, then find pending tasks and dispatch."""
    logger.debug("Scanning for tasks...")
    _check_cancelled_and_timed_out()
    pass


# ── Main loop ─────────────────────────────────────────────────────────────────


def main():
    logger.info(
        f"Worker started. Poll interval={POLL_INTERVAL}s, max_concurrent={MAX_CONCURRENT}, timeout={TASK_TIMEOUT}s"
    )
    logger.info("Press Ctrl+C to stop.")

    while _running:
        _scan_and_run()
        # Sleep in small increments so SIGINT is handled quickly
        for _ in range(POLL_INTERVAL * 10):
            if not _running:
                break
            time.sleep(0.1)

    logger.info("Worker stopped.")


if __name__ == "__main__":
    main()
