"""
PLC TCP/IP Bridge
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""
import time
from collections import deque
from typing import Optional


class FrequencyMonitor:
    """Monitor and display loop frequency"""

    def __init__(self, print_interval: float = 1.0):
        self.print_interval = print_interval
        self.last_print_time = time.time()
        self.loop_count = 0

    def tick(self) -> Optional[float]:
        """Call once per loop iteration. Returns frequency when ready to print."""
        self.loop_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_print_time

        if elapsed >= self.print_interval:
            frequency = self.loop_count / elapsed
            self.loop_count = 0
            self.last_print_time = current_time
            return frequency
        return None

    def print_if_ready(self, prefix: str = "Loop frequency"):
        """Tick and print if interval elapsed"""
        freq = self.tick()
        if freq is not None:
            print(f"{prefix}: {freq:.2f} Hz")


class MovingAverageFrequency:
    """Calculate smoothed loop frequency using moving average"""

    def __init__(self, window_size: int = 100):
        self.times = deque(maxlen=window_size)
        self.last_time = time.perf_counter()

    def tick(self) -> Optional[float]:
        """Call once per loop. Returns frequency when window is full."""
        current_time = time.perf_counter()
        delta = current_time - self.last_time
        self.last_time = current_time
        self.times.append(delta)

        if len(self.times) == self.times.maxlen:
            avg_time = sum(self.times) / len(self.times)
            return 1.0 / avg_time if avg_time > 0 else 0
        return None

    def get_frequency(self) -> float:
        """Get current frequency (returns 0 if not enough samples)"""
        if len(self.times) == 0:
            return 0.0
        avg_time = sum(self.times) / len(self.times)
        return 1.0 / avg_time if avg_time > 0 else 0.0


class InstantFrequency:
    """Calculate instantaneous loop frequency"""

    def __init__(self):
        self.last_time = time.perf_counter()

    def tick(self) -> float:
        """Call once per loop. Returns current frequency."""
        current_time = time.perf_counter()
        delta = current_time - self.last_time
        self.last_time = current_time
        return 1.0 / delta if delta > 0 else 0.0

    def print_inline(self, prefix: str = "Freq"):
        """Print frequency on same line (overwrites)"""
        freq = self.tick()
        print(f"{prefix}: {freq:.2f} Hz", end='\r', flush=True)


class RateLimiter:
    """Limit loop execution rate to target frequency"""

    def __init__(self, target_hz: float):
        self.target_period = 1.0 / target_hz
        self.last_time = time.perf_counter()

    def sleep(self):
        """Sleep to maintain target rate"""
        current_time = time.perf_counter()
        elapsed = current_time - self.last_time
        sleep_time = self.target_period - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)

        self.last_time = time.perf_counter()


class LoopTimer:
    """Measure and track loop timing statistics"""

    def __init__(self):
        self.start_time = None
        self.times = []

    def start(self):
        """Start timing"""
        self.start_time = time.perf_counter()

    def stop(self):
        """Stop timing and record"""
        if self.start_time:
            elapsed = time.perf_counter() - self.start_time
            self.times.append(elapsed)
            self.start_time = None

    def get_stats(self) -> dict:
        """Get timing statistics"""
        if not self.times:
            return {}
        return {
            'min': min(self.times) * 1000,  # ms
            'max': max(self.times) * 1000,  # ms
            'avg': (sum(self.times) / len(self.times)) * 1000,  # ms
            'count': len(self.times)
        }

    def print_stats(self):
        """Print timing statistics"""
        stats = self.get_stats()
        if stats:
            print(f"Loop timing - Min: {stats['min']:.2f}ms, "
                  f"Max: {stats['max']:.2f}ms, "
                  f"Avg: {stats['avg']:.2f}ms, "
                  f"Count: {stats['count']}")

    def reset(self):
        """Reset statistics"""
        self.times = []


class ConnectionMonitor:
    """Monitor connection health and track errors"""

    def __init__(self, alert_threshold: int = 5):
        self.alert_threshold = alert_threshold
        self.total_attempts = 0
        self.successful = 0
        self.failed = 0
        self.consecutive_failures = 0
        self.last_error = None
        self.start_time = time.time()

    def record_success(self):
        """Record successful operation"""
        self.total_attempts += 1
        self.successful += 1
        self.consecutive_failures = 0

    def record_failure(self, error: str = ""):
        """Record failed operation"""
        self.total_attempts += 1
        self.failed += 1
        self.consecutive_failures += 1
        self.last_error = error

        if self.consecutive_failures >= self.alert_threshold:
            print(f"WARNING: {self.consecutive_failures} consecutive failures!")

    def get_stats(self) -> dict:
        """Get connection statistics"""
        uptime = time.time() - self.start_time
        success_rate = (self.successful / self.total_attempts * 100) if self.total_attempts > 0 else 0
        return {
            'total': self.total_attempts,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': success_rate,
            'consecutive_failures': self.consecutive_failures,
            'uptime': uptime
        }

    def print_stats(self):
        """Print connection statistics"""
        stats = self.get_stats()
        print(f"Connection Stats - Total: {stats['total']}, "
              f"Success: {stats['successful']}, "
              f"Failed: {stats['failed']}, "
              f"Success Rate: {stats['success_rate']:.1f}%, "
              f"Uptime: {stats['uptime']:.1f}s")

    def reset(self):
        """Reset statistics"""
        self.total_attempts = 0
        self.successful = 0
        self.failed = 0
        self.consecutive_failures = 0
        self.start_time = time.time()


class DataLogger:
    """Simple data logger for PLC values"""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.logs = deque(maxlen=max_entries)

    def log(self, data: dict):
        """Log data with timestamp"""
        entry = {
            'timestamp': time.time(),
            'data': data.copy()
        }
        self.logs.append(entry)

    def get_last(self, n: int = 10) -> list:
        """Get last n entries"""
        return list(self.logs)[-n:]

    def save_to_file(self, filename: str):
        """Save logs to file"""
        import json
        with open(filename, 'w') as f:
            json.dump(list(self.logs), f, indent=2)
        print(f"Saved {len(self.logs)} entries to {filename}")

    def clear(self):
        """Clear all logs"""
        self.logs.clear()


class Watchdog:
    """Watchdog timer to detect stalled loops"""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.last_kick = time.time()
        self.triggered = False

    def kick(self):
        """Reset watchdog timer"""
        self.last_kick = time.time()
        self.triggered = False

    def check(self) -> bool:
        """Check if watchdog expired. Returns True if timeout exceeded."""
        elapsed = time.time() - self.last_kick
        if elapsed > self.timeout and not self.triggered:
            self.triggered = True
            print(f"WATCHDOG: No activity for {elapsed:.1f}s!")
            return True
        return False

    def is_healthy(self) -> bool:
        """Check if watchdog is healthy"""
        return (time.time() - self.last_kick) < self.timeout


# Usage examples
if __name__ == "__main__":
    # Example 1: Simple frequency monitor
    print("=== FrequencyMonitor Example ===")
    freq_mon = FrequencyMonitor(print_interval=1.0)
    for i in range(1000):
        time.sleep(0.01)  # Simulate work
        freq_mon.print_if_ready("Client loop")

    # Example 2: Moving average
    print("\n=== MovingAverageFrequency Example ===")
    avg_freq = MovingAverageFrequency(window_size=50)
    for i in range(200):
        time.sleep(0.01)
        freq = avg_freq.tick()
        if freq and i % 50 == 0:
            print(f"Smoothed frequency: {freq:.2f} Hz")

    # Example 3: Rate limiter
    print("\n=== RateLimiter Example ===")
    limiter = RateLimiter(target_hz=50)
    start = time.time()
    for i in range(100):
        # Your work here
        limiter.sleep()
    elapsed = time.time() - start
    print(f"100 loops at 50Hz took {elapsed:.2f}s (expected ~2s)")

    # Example 4: Loop timer
    print("\n=== LoopTimer Example ===")
    timer = LoopTimer()
    for i in range(100):
        timer.start()
        time.sleep(0.01)  # Simulate work
        timer.stop()
    timer.print_stats()

    # Example 5: Connection monitor
    print("\n=== ConnectionMonitor Example ===")
    conn_mon = ConnectionMonitor(alert_threshold=3)
    for i in range(20):
        if i % 5 == 0:
            conn_mon.record_failure("Timeout")
        else:
            conn_mon.record_success()
    conn_mon.print_stats()

    # Example 6: Data logger
    print("\n=== DataLogger Example ===")
    logger = DataLogger(max_entries=5)
    for i in range(10):
        logger.log({'temp': 20 + i, 'pressure': 100 + i * 2})
    print(f"Last 3 entries: {logger.get_last(3)}")

    # Example 7: Watchdog
    print("\n=== Watchdog Example ===")
    watchdog = Watchdog(timeout=2.0)
    for i in range(5):
        time.sleep(0.5)
        watchdog.kick()
        print(f"Loop {i}, healthy: {watchdog.is_healthy()}")
    time.sleep(2.5)
    watchdog.check()  # Should trigger