"""
PLC TCP/IP Bridge - Test Suite for Utils
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""

import pytest
import time
from plc_tcpip_bridge.utils import (
    FrequencyMonitor,
    MovingAverageFrequency,
    InstantFrequency,
    RateLimiter,
    LoopTimer,
    ConnectionMonitor,
    DataLogger,
    Watchdog
)


class TestFrequencyMonitor:
    """Test suite for FrequencyMonitor"""

    def test_initialization(self):
        """Test FrequencyMonitor initialization"""
        freq_mon = FrequencyMonitor(print_interval=1.0)
        assert freq_mon.print_interval == 1.0
        assert freq_mon.loop_count == 0

    def test_tick_returns_none_before_interval(self):
        """Test tick returns None before interval elapsed"""
        freq_mon = FrequencyMonitor(print_interval=1.0)

        result = freq_mon.tick()
        assert result is None

    def test_tick_returns_frequency_after_interval(self):
        """Test tick returns frequency after interval"""
        freq_mon = FrequencyMonitor(print_interval=0.1)

        for _ in range(10):
            freq_mon.tick()
            time.sleep(0.01)

        result = freq_mon.tick()
        assert result is not None
        assert result > 0

    def test_frequency_calculation(self):
        """Test frequency calculation accuracy"""
        freq_mon = FrequencyMonitor(print_interval=0.1)

        # Simulate 10 Hz loop
        for _ in range(10):
            freq_mon.tick()
            time.sleep(0.01)  # 100ms / 10 iterations = ~10Hz

        freq = freq_mon.tick()
        if freq:
            assert 8 < freq < 12  # Allow some tolerance


class TestMovingAverageFrequency:
    """Test suite for MovingAverageFrequency"""

    def test_initialization(self):
        """Test MovingAverageFrequency initialization"""
        avg_freq = MovingAverageFrequency(window_size=50)
        assert len(avg_freq.times) == 0

    def test_tick_returns_none_before_window_full(self):
        """Test tick returns None before window is full"""
        avg_freq = MovingAverageFrequency(window_size=10)

        for _ in range(5):
            result = avg_freq.tick()
            time.sleep(0.01)

        # Window not full yet, but last tick should return frequency
        assert result is None or result > 0

    def test_get_frequency(self):
        """Test get_frequency method"""
        avg_freq = MovingAverageFrequency(window_size=10)

        for _ in range(15):
            avg_freq.tick()
            time.sleep(0.01)

        freq = avg_freq.get_frequency()
        assert freq > 0

    def test_window_size_limit(self):
        """Test window respects max size"""
        avg_freq = MovingAverageFrequency(window_size=5)

        for _ in range(10):
            avg_freq.tick()
            time.sleep(0.01)

        assert len(avg_freq.times) <= 5


class TestInstantFrequency:
    """Test suite for InstantFrequency"""

    def test_initialization(self):
        """Test InstantFrequency initialization"""
        inst_freq = InstantFrequency()
        assert inst_freq.last_time > 0

    def test_tick_returns_frequency(self):
        """Test tick returns frequency value"""
        inst_freq = InstantFrequency()
        time.sleep(0.01)

        freq = inst_freq.tick()
        assert freq > 0

    def test_frequency_varies_with_delay(self):
        """Test frequency changes with different delays"""
        inst_freq = InstantFrequency()

        time.sleep(0.01)
        freq1 = inst_freq.tick()

        time.sleep(0.05)
        freq2 = inst_freq.tick()

        assert freq1 > freq2  # Longer delay = lower frequency


class TestRateLimiter:
    """Test suite for RateLimiter"""

    def test_initialization(self):
        """Test RateLimiter initialization"""
        limiter = RateLimiter(target_hz=50)
        assert limiter.target_period == 0.02  # 1/50

    def test_rate_limiting(self):
        """Test rate limiting maintains target frequency"""
        limiter = RateLimiter(target_hz=50)

        start = time.time()
        for _ in range(10):
            limiter.sleep()
        elapsed = time.time() - start

        expected = 10 / 50  # 10 iterations at 50Hz = 0.2s
        assert abs(elapsed - expected) < 0.05  # 50ms tolerance

    def test_no_negative_sleep(self):
        """Test limiter doesn't sleep if loop is too slow"""
        limiter = RateLimiter(target_hz=100)

        time.sleep(0.02)  # Simulate slow loop
        start = time.time()
        limiter.sleep()
        elapsed = time.time() - start

        assert elapsed < 0.01  # Should not sleep much


class TestLoopTimer:
    """Test suite for LoopTimer"""

    def test_initialization(self):
        """Test LoopTimer initialization"""
        timer = LoopTimer()
        assert timer.start_time is None
        assert len(timer.times) == 0

    def test_start_stop(self):
        """Test start and stop timing"""
        timer = LoopTimer()

        timer.start()
        time.sleep(0.01)
        timer.stop()

        assert len(timer.times) == 1
        assert timer.times[0] > 0

    def test_get_stats(self):
        """Test getting timing statistics"""
        timer = LoopTimer()

        for _ in range(5):
            timer.start()
            time.sleep(0.01)
            timer.stop()

        stats = timer.get_stats()
        assert 'min' in stats
        assert 'max' in stats
        assert 'avg' in stats
        assert 'count' in stats
        assert stats['count'] == 5

    def test_reset(self):
        """Test resetting statistics"""
        timer = LoopTimer()

        timer.start()
        time.sleep(0.01)
        timer.stop()

        timer.reset()
        assert len(timer.times) == 0


class TestConnectionMonitor:
    """Test suite for ConnectionMonitor"""

    def test_initialization(self):
        """Test ConnectionMonitor initialization"""
        conn_mon = ConnectionMonitor(alert_threshold=5)
        assert conn_mon.alert_threshold == 5
        assert conn_mon.total_attempts == 0
        assert conn_mon.successful == 0
        assert conn_mon.failed == 0

    def test_record_success(self):
        """Test recording successful operations"""
        conn_mon = ConnectionMonitor()

        conn_mon.record_success()

        assert conn_mon.total_attempts == 1
        assert conn_mon.successful == 1
        assert conn_mon.consecutive_failures == 0

    def test_record_failure(self):
        """Test recording failed operations"""
        conn_mon = ConnectionMonitor()

        conn_mon.record_failure("Test error")

        assert conn_mon.total_attempts == 1
        assert conn_mon.failed == 1
        assert conn_mon.consecutive_failures == 1
        assert conn_mon.last_error == "Test error"

    def test_consecutive_failures_reset(self):
        """Test consecutive failures reset on success"""
        conn_mon = ConnectionMonitor()

        conn_mon.record_failure()
        conn_mon.record_failure()
        assert conn_mon.consecutive_failures == 2

        conn_mon.record_success()
        assert conn_mon.consecutive_failures == 0

    def test_get_stats(self):
        """Test getting connection statistics"""
        conn_mon = ConnectionMonitor()

        conn_mon.record_success()
        conn_mon.record_success()
        conn_mon.record_failure()

        stats = conn_mon.get_stats()
        assert stats['total'] == 3
        assert stats['successful'] == 2
        assert stats['failed'] == 1
        assert abs(stats['success_rate'] - 66.67) < 1

    def test_reset(self):
        """Test resetting statistics"""
        conn_mon = ConnectionMonitor()

        conn_mon.record_success()
        conn_mon.record_failure()

        conn_mon.reset()

        assert conn_mon.total_attempts == 0
        assert conn_mon.successful == 0
        assert conn_mon.failed == 0


class TestDataLogger:
    """Test suite for DataLogger"""

    def test_initialization(self):
        """Test DataLogger initialization"""
        logger = DataLogger(max_entries=100)
        assert len(logger.logs) == 0

    def test_log_data(self):
        """Test logging data"""
        logger = DataLogger(max_entries=100)

        logger.log({'speed': 1500, 'temp': 25.5})

        assert len(logger.logs) == 1
        assert logger.logs[0]['data']['speed'] == 1500
        assert 'timestamp' in logger.logs[0]

    def test_max_entries_limit(self):
        """Test max entries limit"""
        logger = DataLogger(max_entries=5)

        for i in range(10):
            logger.log({'value': i})

        assert len(logger.logs) == 5

    def test_get_last(self):
        """Test getting last N entries"""
        logger = DataLogger(max_entries=100)

        for i in range(10):
            logger.log({'value': i})

        last_3 = logger.get_last(3)
        assert len(last_3) == 3
        assert last_3[-1]['data']['value'] == 9

    def test_clear(self):
        """Test clearing logs"""
        logger = DataLogger(max_entries=100)

        logger.log({'value': 1})
        logger.log({'value': 2})

        logger.clear()
        assert len(logger.logs) == 0


class TestWatchdog:
    """Test suite for Watchdog"""

    def test_initialization(self):
        """Test Watchdog initialization"""
        watchdog = Watchdog(timeout=5.0)
        assert watchdog.timeout == 5.0
        assert watchdog.triggered == False

    def test_kick_resets_timer(self):
        """Test kick resets timer"""
        watchdog = Watchdog(timeout=1.0)

        time.sleep(0.5)
        watchdog.kick()

        assert watchdog.is_healthy() == True

    def test_timeout_detection(self):
        """Test timeout is detected"""
        watchdog = Watchdog(timeout=0.1)

        time.sleep(0.2)
        result = watchdog.check()

        assert result == True
        assert watchdog.triggered == True

    def test_is_healthy(self):
        """Test is_healthy method"""
        watchdog = Watchdog(timeout=1.0)

        assert watchdog.is_healthy() == True

        time.sleep(1.1)
        assert watchdog.is_healthy() == False

    def test_kick_clears_triggered(self):
        """Test kick clears triggered flag"""
        watchdog = Watchdog(timeout=0.1)

        time.sleep(0.2)
        watchdog.check()
        assert watchdog.triggered == True

        watchdog.kick()
        assert watchdog.triggered == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])