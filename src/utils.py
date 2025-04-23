"""
Utility functions for error handling, retry logic, and common operations
"""

import asyncio
import logging
import functools
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for async functions with exponential backoff retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        break

                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay:.1f}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return wrapper
    return decorator


def rate_limit(calls_per_minute: int = 60):
    """
    Decorator to rate limit function calls
    """
    min_interval = 60.0 / calls_per_minute
    last_called = {}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            func_key = f"{func.__name__}_{id(func)}"
            now = time.time()

            if func_key in last_called:
                elapsed = now - last_called[func_key]
                if elapsed < min_interval:
                    sleep_time = min_interval - elapsed
                    logger.debug(f"Rate limiting {func.__name__}: sleeping {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)

            last_called[func_key] = time.time()
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            func_key = f"{func.__name__}_{id(func)}"
            now = time.time()

            if func_key in last_called:
                elapsed = now - last_called[func_key]
                if elapsed < min_interval:
                    sleep_time = min_interval - elapsed
                    logger.debug(f"Rate limiting {func.__name__}: sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)

            last_called[func_key] = time.time()
            return func(*args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for API calls
    """
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def _should_attempt_reset(self) -> bool:
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.timeout)

    def _on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker OPEN - {self.failure_count} failures")


def safe_json_parse(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with error handling
    """
    try:
        import json
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.debug(f"JSON parse error: {e}")
        return default


def clean_text(text: str, max_length: int = 200) -> str:
    """
    Clean and truncate text for display
    """
    if not text:
        return ""

    # Remove extra whitespace and newlines
    cleaned = ' '.join(text.split())

    # Truncate if necessary
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."

    return cleaned


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human readable string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def is_business_hours(timezone: str = 'UTC') -> bool:
    """
    Check if current time is within business hours (9 AM - 6 PM)
    """
    try:
        import pytz
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return 9 <= now.hour < 18
    except Exception:
        # Fallback to UTC if timezone handling fails
        now = datetime.utcnow()
        return 9 <= now.hour < 18


def calculate_trend_momentum(scores: list, time_window: int = 5) -> float:
    """
    Calculate trend momentum based on recent score changes
    """
    if len(scores) < 2:
        return 0.0

    recent_scores = scores[-time_window:] if len(scores) >= time_window else scores
    if len(recent_scores) < 2:
        return 0.0

    # Calculate rate of change
    time_diff = len(recent_scores) - 1
    score_diff = recent_scores[-1] - recent_scores[0]

    momentum = score_diff / time_diff if time_diff > 0 else 0.0
    return momentum


class HealthChecker:
    """
    System health monitoring for API clients and database
    """
    def __init__(self):
        self.last_checks = {}
        self.health_status = {}

    async def check_api_health(self, api_name: str, check_func: Callable) -> bool:
        """
        Check health of an API endpoint
        """
        try:
            start_time = time.time()
            await check_func()
            response_time = time.time() - start_time

            self.health_status[api_name] = {
                'status': 'healthy',
                'response_time': response_time,
                'last_check': datetime.now(),
                'error': None
            }

            logger.debug(f"{api_name} health check passed ({response_time:.2f}s)")
            return True

        except Exception as e:
            self.health_status[api_name] = {
                'status': 'unhealthy',
                'response_time': None,
                'last_check': datetime.now(),
                'error': str(e)
            }

            logger.warning(f"{api_name} health check failed: {e}")
            return False

    def get_system_health(self) -> dict:
        """
        Get overall system health status
        """
        healthy_services = sum(1 for status in self.health_status.values()
                             if status['status'] == 'healthy')
        total_services = len(self.health_status)

        return {
            'overall_status': 'healthy' if healthy_services == total_services else 'degraded',
            'healthy_services': healthy_services,
            'total_services': total_services,
            'services': self.health_status,
            'timestamp': datetime.now()
        }