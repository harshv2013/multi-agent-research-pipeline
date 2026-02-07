"""
Rate limiting utilities for API calls.

Demonstrates:
- Token bucket algorithm
- Request rate limiting
- Concurrent request management
- Quota tracking
"""
import time
import asyncio
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import threading


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int
    tokens_per_minute: int
    max_concurrent: int = 5
    
    @property
    def min_request_interval(self) -> float:
        """Minimum seconds between requests."""
        return 60.0 / self.requests_per_minute


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.
    
    Each request consumes tokens. Tokens refill at a constant rate.
    If insufficient tokens, request is delayed until tokens available.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens (burst capacity)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed, False if insufficient
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_tokens(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until tokens available.
        
        Args:
            tokens: Number of tokens needed
            timeout: Maximum wait time in seconds
            
        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.consume(tokens):
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            # Calculate wait time
            with self.lock:
                self._refill()
                deficit = tokens - self.tokens
                wait_time = deficit / self.refill_rate
            
            time.sleep(min(wait_time, 0.1))  # Sleep in small increments
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def available_tokens(self) -> int:
        """Get current available tokens."""
        with self.lock:
            self._refill()
            return int(self.tokens)


class RateLimiter:
    """
    Comprehensive rate limiter for API requests.
    
    Tracks:
    - Requests per minute
    - Tokens per minute
    - Concurrent requests
    - Request history
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        
        # Token buckets
        self.request_bucket = TokenBucket(
            capacity=config.requests_per_minute,
            refill_rate=config.requests_per_minute / 60.0
        )
        self.token_bucket = TokenBucket(
            capacity=config.tokens_per_minute,
            refill_rate=config.tokens_per_minute / 60.0
        )
        
        # Concurrent request tracking
        self.active_requests = 0
        self.max_concurrent = config.max_concurrent
        self.concurrent_lock = threading.Lock()
        
        # Request history (last 60 seconds)
        self.request_history: deque = deque(maxlen=1000)
    
    def acquire(self, estimated_tokens: int = 1000, timeout: Optional[float] = 30.0) -> bool:
        """
        Acquire permission to make request.
        
        Args:
            estimated_tokens: Estimated tokens for this request
            timeout: Maximum wait time
            
        Returns:
            True if acquired, False if timeout or limit exceeded
        """
        start_time = time.time()
        
        # Wait for concurrent slot
        while True:
            with self.concurrent_lock:
                if self.active_requests < self.max_concurrent:
                    self.active_requests += 1
                    break
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.1)
        
        # Wait for rate limit tokens
        request_acquired = self.request_bucket.wait_for_tokens(1, timeout)
        token_acquired = self.token_bucket.wait_for_tokens(estimated_tokens, timeout)
        
        if not (request_acquired and token_acquired):
            # Release concurrent slot if we couldn't acquire rate limit
            with self.concurrent_lock:
                self.active_requests -= 1
            return False
        
        # Record request
        self.request_history.append({
            'timestamp': datetime.now(),
            'estimated_tokens': estimated_tokens
        })
        
        return True
    
    def release(self, actual_tokens: Optional[int] = None):
        """
        Release concurrent slot after request completes.
        
        Args:
            actual_tokens: Actual tokens used (for adjustment)
        """
        with self.concurrent_lock:
            self.active_requests = max(0, self.active_requests - 1)
        
        # Adjust token bucket if actual usage known
        if actual_tokens:
            # This is informational; token bucket already consumed estimated
            pass
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        # Count requests in last minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_requests = [
            r for r in self.request_history 
            if r['timestamp'] > one_minute_ago
        ]
        
        return {
            'active_requests': self.active_requests,
            'max_concurrent': self.max_concurrent,
            'requests_last_minute': len(recent_requests),
            'requests_per_minute_limit': self.config.requests_per_minute,
            'available_request_tokens': self.request_bucket.available_tokens(),
            'available_api_tokens': self.token_bucket.available_tokens(),
            'tokens_per_minute_limit': self.config.tokens_per_minute
        }
    
    def __enter__(self):
        """Context manager entry."""
        success = self.acquire()
        if not success:
            raise RuntimeError("Failed to acquire rate limit within timeout")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()