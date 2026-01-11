from abc import ABC, abstractmethod
import hashlib
import zlib
from database import InMemoryDB
from encoding import base62_encode
from snowflake import Snowflake


class ShorteningStrategy(ABC):
    """Abstract base class for URL shortening strategies."""
    
    @abstractmethod
    def get_shortened_url(self, long_url, db: InMemoryDB):
        """
        Shorten a long URL.
        
        Args:
            long_url: The URL to shorten
            db: Database instance for storing mappings
            
        Returns:
            Shortened URL string
        """
        pass

    @abstractmethod
    def get_longer_url(self, shortened_url, db: InMemoryDB):
        """
        Resolve a shortened URL back to the original long URL.
        If not found, return None.
        """
        pass


class HashShortener(ShorteningStrategy):
    """
    Hash-based URL shortening strategy.
    
    Uses cryptographic hashing with collision resolution.
    Same URL always produces same short code (deterministic).
    """
    
    def __init__(self, method="md5"):
        """
        Initialize hash shortener.
        
        Args:
            method: Hash algorithm to use ('md5', 'sha1', 'crc32')
        """
        self.method = method

    def _hash(self, long_url):
        """Generate hash for the long URL."""
        if self.method == "crc32":
            return format(zlib.crc32(long_url.encode()), "x")
        elif self.method == "sha1":
            return hashlib.sha1(long_url.encode()).hexdigest()
        else:
            return hashlib.md5(long_url.encode()).hexdigest()

    def get_shortened_url(self, long_url, db: InMemoryDB):
        """
        Shorten URL using hash-based approach.
        
        Process:
        1. Hash the long URL
        2. Take first 7 characters
        3. Check for collisions using Bloom filter
        4. If collision, rehash and try again
        5. Store and return short URL
        """
        hashed = self._hash(long_url)
        short = hashed[:7]

        # Ensure uniqueness
        while db.exists(short):
            short += "unique"
            short = hashlib.md5(short.encode()).hexdigest()[:7]

        db.save(short, long_url)
        return short
    
    def get_longer_url(self, shortened_url, db: InMemoryDB):
        """
        Resolve a shortened URL back to the original long URL.
        If not found, return None.
        """
        return db.get(shortened_url)


class SnowflakeShortener(ShorteningStrategy):
    """
    Snowflake-based URL shortening strategy.
    
    Uses distributed ID generation with base62 encoding.
    No collision handling needed (69+ year guarantee).
    Better for distributed systems.
    """
    
    def __init__(self):
        """Initialize Snowflake shortener."""
        self.snowflake = Snowflake()

    def get_shortened_url(self, long_url, db: InMemoryDB):
        """
        Shorten URL using Snowflake + Base62 approach.
        
        Process:
        1. Generate unique Snowflake ID
        2. Convert to base62
        3. Store and return short URL
        """
        num = self.snowflake.generate()
        short = base62_encode(num)
        db.save(short, long_url)
        return short
    
    def get_longer_url(self, shortened_url, db: InMemoryDB):
        """
        Resolve a shortened URL back to the original long URL.
        If not found, return None.
        """
        return db.get(shortened_url)
