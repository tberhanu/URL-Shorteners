from bloom_filter import SimpleBloomFilter


class InMemoryDB:
    """
    In-memory database for storing short URL to long URL mappings.
    Uses a Bloom filter for fast existence checks.
    """
    
    def __init__(self):
        self.map = {}  # short → long
        self.bloom = SimpleBloomFilter()

    def exists(self, short_url):
        """Check if a short URL exists using Bloom filter."""
        return self.bloom.contains(short_url)

    def save(self, short_url, long_url):
        """Save a short URL to long URL mapping."""
        self.map[short_url] = long_url
        self.bloom.add(short_url)

    def get(self, short_url):
        """Retrieve the long URL for a given short URL."""
        return self.map.get(short_url, None)
