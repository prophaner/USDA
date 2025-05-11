"""
Rate limiter service for API calls.
Implements a sliding window rate limit for USDA API calls.
"""
import time
from collections import deque
from typing import Dict, Deque, Tuple
import threading

class RateLimiter:
    """
    Rate limiter using a sliding window algorithm.
    Tracks requests per IP address and enforces limits.
    """
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store timestamps of requests for each IP
        self.request_logs: Dict[str, Deque[float]] = {}
        # Lock for thread safety
        self.lock = threading.RLock()
    
    def check_limit(self, ip_address: str) -> Tuple[bool, int]:
        """
        Check if a request from the given IP is allowed without incrementing the counter.
        
        Args:
            ip_address: The IP address making the request
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        with self.lock:
            # Initialize if this is the first request from this IP
            if ip_address not in self.request_logs:
                self.request_logs[ip_address] = deque()
            
            # Get the current time
            current_time = time.time()
            
            # Remove timestamps outside the window
            self._clean_old_requests(ip_address, current_time)
            
            # Check if we're at the limit
            current_count = len(self.request_logs[ip_address])
            if current_count >= self.max_requests:
                remaining = 0
                return False, remaining
            
            # Calculate remaining requests
            remaining = self.max_requests - current_count
            return True, remaining
    
    def increment(self, ip_address: str) -> Tuple[bool, int]:
        """
        Increment the counter for the given IP address and check if it's allowed.
        
        Args:
            ip_address: The IP address making the request
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        with self.lock:
            # Initialize if this is the first request from this IP
            if ip_address not in self.request_logs:
                self.request_logs[ip_address] = deque()
            
            # Get the current time
            current_time = time.time()
            
            # Remove timestamps outside the window
            self._clean_old_requests(ip_address, current_time)
            
            # Check if we're at the limit
            if len(self.request_logs[ip_address]) >= self.max_requests:
                remaining = 0
                return False, remaining
            
            # Add the current request timestamp
            self.request_logs[ip_address].append(current_time)
            
            # Calculate remaining requests
            remaining = self.max_requests - len(self.request_logs[ip_address])
            return True, remaining
    
    def _clean_old_requests(self, ip_address: str, current_time: float) -> None:
        """
        Remove timestamps that are outside the current window.
        
        Args:
            ip_address: The IP address to clean
            current_time: The current timestamp
        """
        window_start = current_time - self.window_seconds
        
        # Remove old timestamps
        while (self.request_logs[ip_address] and 
               self.request_logs[ip_address][0] < window_start):
            self.request_logs[ip_address].popleft()

# Create a global rate limiter instance
# 1,000 requests per hour (3600 seconds)
usda_rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)