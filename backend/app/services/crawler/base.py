from abc import ABC, abstractmethod
import time
import random
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.schemas.job import JobCreate

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    """Exception raised when the circuit breaker is open and requests are fast-failed."""
    pass

class BaseCrawler(ABC):
    # Class-level state to persist circuit breaker across worker threads/runs
    # Format: {crawler_name: {"failures": int, "status": str, "tripped_at": Optional[datetime]}}
    _circuit_state: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        name: str,
        rate_limit_delay: float = 1.0,  # 1 second delay between fetches
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        consecutive_failures_limit: int = 5,
        circuit_breaker_cooldown: int = 600  # 10 minutes in seconds
    ):
        self.name = name.lower()
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.consecutive_failures_limit = consecutive_failures_limit
        self.circuit_breaker_cooldown = circuit_breaker_cooldown
        
        # Initialize circuit state for this crawler if not present
        if self.name not in BaseCrawler._circuit_state:
            BaseCrawler._circuit_state[self.name] = {
                "failures": 0,
                "status": "closed",  # closed, open
                "tripped_at": None
            }

    @abstractmethod
    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from the target source."""
        pass

    def _check_circuit(self):
        """Check if the circuit is open. If open and cooldown passed, reset to closed."""
        state = BaseCrawler._circuit_state[self.name]
        if state["status"] == "open":
            tripped_at = state["tripped_at"]
            if tripped_at:
                elapsed = (datetime.now(timezone.utc) - tripped_at).total_seconds()
                if elapsed > self.circuit_breaker_cooldown:
                    # Cooldown has passed, reset circuit
                    logger.info(f"[CircuitBreaker] Cooldown elapsed for '{self.name}'. Resetting circuit to CLOSED.")
                    state["status"] = "closed"
                    state["failures"] = 0
                    state["tripped_at"] = None
                else:
                    logger.warning(f"[CircuitBreaker] Circuit is OPEN for '{self.name}'. Fast-failing request. ({int(self.circuit_breaker_cooldown - elapsed)}s remaining)")
                    raise CircuitBreakerOpenException(f"Circuit breaker is OPEN for crawler '{self.name}' due to repeated failures.")

    def _record_success(self):
        """Reset consecutive failures count upon a successful request."""
        state = BaseCrawler._circuit_state[self.name]
        state["failures"] = 0
        state["status"] = "closed"
        state["tripped_at"] = None

    def _record_failure(self):
        """Increment failure count and trip the circuit if threshold is reached."""
        state = BaseCrawler._circuit_state[self.name]
        state["failures"] += 1
        logger.warning(f"[CircuitBreaker] Recorded failure for '{self.name}'. Consecutive failures: {state['failures']}/{self.consecutive_failures_limit}")
        
        if state["failures"] >= self.consecutive_failures_limit:
            state["status"] = "open"
            state["tripped_at"] = datetime.now(timezone.utc)
            logger.error(f"[CircuitBreaker] !!! CIRCUIT TRIPPED OPEN for '{self.name}' !!! Cooldown active for {self.circuit_breaker_cooldown} seconds.")

    def request_with_retry(
        self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> requests.Response:
        """Execute an HTTP request incorporating exponential backoff with jitter and circuit breaker policies."""
        # 1. Respect Circuit Breaker
        self._check_circuit()
        
        # 2. Respect Rate Limiting
        time.sleep(self.rate_limit_delay)
        
        attempt = 0
        current_delay = self.initial_delay
        
        while attempt < self.max_retries:
            try:
                logger.info(f"[{self.name}] Fetching {url} - Attempt {attempt + 1}/{self.max_retries}")
                response = requests.request(method, url, headers=headers, timeout=10, **kwargs)
                
                # Check for HTTP status errors (raise_for_status throws HTTPError)
                response.raise_for_status()
                
                # Successful call
                self._record_success()
                return response
                
            except (requests.RequestException, Exception) as e:
                attempt += 1
                logger.warning(f"[{self.name}] Request failed: {str(e)}. Attempt {attempt} failed.")
                
                if attempt == self.max_retries:
                    self._record_failure()
                    raise e
                
                # Calculate exponential delay with random jitter (0% to 50% random addition)
                jitter = random.uniform(0, 0.5) * current_delay
                sleep_time = current_delay + jitter
                logger.info(f"[{self.name}] Backing off. Sleeping for {sleep_time:.2f} seconds before retry.")
                time.sleep(sleep_time)
                
                current_delay *= self.backoff_factor

        raise requests.RequestException(f"[{self.name}] Maximum retries reached for request: {url}")
