from database import InMemoryDB
from strategies import ShorteningStrategy


class URLShortener:
    """
    Context class implementing the Strategy pattern.
    Provides a unified interface for URL shortening with pluggable strategies.
    """
    
    def __init__(self, strategy: ShorteningStrategy):
        """
        Initialize URL shortener with a strategy.
        
        Args:
            strategy: ShorteningStrategy implementation to use
        """
        self.strategy = strategy
        self.db = InMemoryDB()

    def set_strategy(self, strategy: ShorteningStrategy):
        """
        Switch to a different shortening strategy at runtime.
        
        Args:
            strategy: New ShorteningStrategy implementation to use
        """
        self.strategy = strategy

    def shorten(self, long_url):
        """
        Shorten a long URL using the current strategy.
        
        Args:
            long_url: The URL to shorten
            
        Returns:
            Shortened URL string
        """
        return self.strategy.get_shortened_url(long_url, self.db)

    def resolve(self, short_url):
        """
        Resolve a short URL back to the original long URL.
        
        Args:
            short_url: The shortened URL
            
        Returns:
            Original long URL or None if not found
        """
        return self.strategy.get_longer_url(short_url, self.db)
