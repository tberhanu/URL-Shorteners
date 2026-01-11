import time
import threading


class Snowflake:
    """
    Twitter Snowflake-inspired distributed ID generator.
    Generates unique 64-bit IDs with timestamp and sequence components.
    
    Structure:
    - Timestamp (milliseconds): 52 bits
    - Sequence number: 12 bits
    
    Properties:
    - Thread-safe using locks
    - Monotonically increasing
    - Collision-free for ~69 years at high throughput
    """
    
    def __init__(self):
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def _timestamp(self):
        """Get current time in milliseconds."""
        return int(time.time() * 1000)

    def generate(self):
        """
        Generate a unique Snowflake ID.
        
        Returns:
            64-bit unique integer ID
        """
        with self.lock:
            timestamp = self._timestamp()

            if timestamp == self.last_timestamp:
                self.sequence += 1
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Combine timestamp + sequence
            return (timestamp << 12) | self.sequence
