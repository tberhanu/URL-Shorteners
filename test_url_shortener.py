import unittest
from url_shortener import URLShortener
from strategies import HashShortener, SnowflakeShortener
from database import InMemoryDB
from bloom_filter import SimpleBloomFilter
from encoding import base62_encode
from snowflake import Snowflake


class TestSimpleBloomFilter(unittest.TestCase):
    """Test cases for SimpleBloomFilter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bloom = SimpleBloomFilter(size=1000)
    
    def test_add_and_contains(self):
        """Test adding and checking if value exists in Bloom filter."""
        value = "test_url"
        self.assertFalse(self.bloom.contains(value))
        self.bloom.add(value)
        self.assertTrue(self.bloom.contains(value))
    
    def test_multiple_adds(self):
        """Test adding multiple values."""
        values = ["url1", "url2", "url3"]
        for value in values:
            self.bloom.add(value)
        
        for value in values:
            self.assertTrue(self.bloom.contains(value))
    
    def test_hashes_returns_three_values(self):
        """Test that _hashes returns exactly three hash values."""
        hashes = self.bloom._hashes("test")
        self.assertEqual(len(hashes), 3)
        self.assertTrue(all(isinstance(h, int) for h in hashes))
    
    def test_hashes_within_bounds(self):
        """Test that all hash values are within bloom filter size."""
        value = "test_url"
        hashes = self.bloom._hashes(value)
        for h in hashes:
            self.assertGreaterEqual(h, 0)
            self.assertLess(h, self.bloom.size)


class TestInMemoryDB(unittest.TestCase):
    """Test cases for InMemoryDB class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = InMemoryDB()
    
    def test_save_and_get(self):
        """Test saving and retrieving a URL mapping."""
        short = "abc123"
        long = "https://example.com/very/long/url"
        self.db.save(short, long)
        self.assertEqual(self.db.get(short), long)
    
    def test_get_nonexistent_url(self):
        """Test getting a URL that doesn't exist."""
        result = self.db.get("nonexistent")
        self.assertIsNone(result)
    
    def test_exists_after_save(self):
        """Test that exists returns True after saving."""
        short = "xyz789"
        self.assertFalse(self.db.exists(short))
        self.db.save(short, "https://example.com")
        self.assertTrue(self.db.exists(short))
    
    def test_multiple_save_and_get(self):
        """Test multiple save and get operations."""
        urls = [
            ("short1", "https://example1.com"),
            ("short2", "https://example2.com"),
            ("short3", "https://example3.com"),
        ]
        
        for short, long in urls:
            self.db.save(short, long)
        
        for short, long in urls:
            self.assertEqual(self.db.get(short), long)


class TestBase62Encoding(unittest.TestCase):
    """Test cases for base62_encode function."""
    
    def test_encode_zero(self):
        """Test encoding zero."""
        result = base62_encode(0)
        self.assertEqual(result, "0")
    
    def test_encode_small_number(self):
        """Test encoding small numbers."""
        self.assertEqual(base62_encode(1), "1")
        self.assertEqual(base62_encode(9), "9")
        self.assertEqual(base62_encode(10), "a")
        self.assertEqual(base62_encode(61), "Z")
    
    def test_encode_large_number(self):
        """Test encoding large numbers."""
        result = base62_encode(1000000)
        self.assertTrue(len(result) > 0)
        self.assertTrue(all(c in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in result))
    
    def test_encode_returns_string(self):
        """Test that encode returns a string."""
        result = base62_encode(12345)
        self.assertIsInstance(result, str)


class TestSnowflake(unittest.TestCase):
    """Test cases for Snowflake ID generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.snowflake = Snowflake()
    
    def test_generate_returns_integer(self):
        """Test that generate returns an integer."""
        result = self.snowflake.generate()
        self.assertIsInstance(result, int)
    
    def test_generate_unique_ids(self):
        """Test that consecutive generates produce different IDs."""
        id1 = self.snowflake.generate()
        id2 = self.snowflake.generate()
        self.assertNotEqual(id1, id2)
    
    def test_generate_multiple_unique(self):
        """Test that multiple IDs are unique."""
        ids = [self.snowflake.generate() for _ in range(100)]
        unique_ids = set(ids)
        self.assertEqual(len(ids), len(unique_ids))
    
    def test_generate_increasing(self):
        """Test that generated IDs are generally increasing."""
        ids = [self.snowflake.generate() for _ in range(10)]
        # Most should be increasing (allowing for same timestamp scenarios)
        increasing_count = sum(1 for i in range(len(ids) - 1) if ids[i] < ids[i + 1])
        self.assertGreaterEqual(increasing_count, len(ids) - 2)


class TestHashShortener(unittest.TestCase):
    """Test cases for HashShortener strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = InMemoryDB()
        self.shortener = HashShortener(method="md5")
    
    def test_get_shortened_url(self):
        """Test shortening a URL."""
        long_url = "https://example.com/very/long/url"
        short = self.shortener.get_shortened_url(long_url, self.db)
        self.assertIsNotNone(short)
        self.assertEqual(len(short), 7)
    
    def test_get_longer_url(self):
        """Test resolving a shortened URL."""
        long_url = "https://example.com/very/long/url"
        short = self.shortener.get_shortened_url(long_url, self.db)
        resolved = self.shortener.get_longer_url(short, self.db)
        self.assertEqual(resolved, long_url)
    
    def test_deterministic_hashing(self):
        """Test that same URL produces same short code."""
        long_url = "https://example.com/test"
        short1 = self.shortener.get_shortened_url(long_url, self.db)
        
        # Create new db to avoid collision checks
        db2 = InMemoryDB()
        short2 = self.shortener.get_shortened_url(long_url, db2)
        
        self.assertEqual(short1, short2)
    
    def test_different_urls_different_codes(self):
        """Test that different URLs produce different short codes."""
        url1 = "https://example.com/url1"
        url2 = "https://example.com/url2"
        
        short1 = self.shortener.get_shortened_url(url1, self.db)
        short2 = self.shortener.get_shortened_url(url2, self.db)
        
        self.assertNotEqual(short1, short2)
    
    def test_hash_methods(self):
        """Test different hash methods."""
        long_url = "https://example.com/test"
        
        for method in ["md5", "sha1", "crc32"]:
            db = InMemoryDB()
            shortener = HashShortener(method=method)
            short = shortener.get_shortened_url(long_url, db)
            self.assertIsNotNone(short)
            self.assertEqual(len(short), 7)
    
    def test_collision_resolution(self):
        """Test that collision resolution works."""
        # This is hard to test directly, but we verify no exception is raised
        # when trying to shorten multiple URLs
        for i in range(5):
            url = f"https://example.com/url{i}"
            short = self.shortener.get_shortened_url(url, self.db)
            self.assertIsNotNone(short)


class TestSnowflakeShortener(unittest.TestCase):
    """Test cases for SnowflakeShortener strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = InMemoryDB()
        self.shortener = SnowflakeShortener()
    
    def test_get_shortened_url(self):
        """Test shortening a URL with Snowflake."""
        long_url = "https://example.com/very/long/url"
        short = self.shortener.get_shortened_url(long_url, self.db)
        self.assertIsNotNone(short)
        self.assertGreater(len(short), 0)
    
    def test_get_longer_url(self):
        """Test resolving a Snowflake shortened URL."""
        long_url = "https://example.com/very/long/url"
        short = self.shortener.get_shortened_url(long_url, self.db)
        resolved = self.shortener.get_longer_url(short, self.db)
        self.assertEqual(resolved, long_url)
    
    def test_unique_shorts_per_call(self):
        """Test that Snowflake IDs are unique even for same URL."""
        url = "https://example.com/test"
        short1 = self.shortener.get_shortened_url(url, self.db)
        
        # Generate more shorts from same URL - they should be different
        # due to Snowflake's incrementing nature
        shorts = [short1]
        for _ in range(5):
            short = self.shortener.get_shortened_url(url, self.db)
            shorts.append(short)
        
        # All shorts should be unique due to different IDs
        self.assertEqual(len(shorts), len(set(shorts)))
    
    def test_multiple_shortens_unique(self):
        """Test that multiple shortenings produce unique codes."""
        shorts = set()
        for i in range(10):
            url = f"https://example.com/url{i}"
            short = self.shortener.get_shortened_url(url, self.db)
            shorts.add(short)
        
        self.assertEqual(len(shorts), 10)


class TestURLShortener(unittest.TestCase):
    """Test cases for URLShortener context class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shortener = URLShortener(HashShortener(method="md5"))
    
    def test_shorten_with_hash_strategy(self):
        """Test shortening URL with Hash strategy."""
        long_url = "https://example.com/very/long/url"
        short = self.shortener.shorten(long_url)
        self.assertIsNotNone(short)
        self.assertEqual(len(short), 7)
    
    def test_resolve_shortened_url(self):
        """Test resolving a shortened URL."""
        long_url = "https://example.com/very/long/url"
        short = self.shortener.shorten(long_url)
        resolved = self.shortener.resolve(short)
        self.assertEqual(resolved, long_url)
    
    def test_resolve_nonexistent(self):
        """Test resolving a non-existent short URL."""
        result = self.shortener.resolve("nonexistent")
        self.assertIsNone(result)
    
    def test_set_strategy(self):
        """Test switching strategies at runtime."""
        long_url = "https://example.com/test"
        
        # Use Hash strategy
        short1 = self.shortener.shorten(long_url)
        resolved1 = self.shortener.resolve(short1)
        self.assertEqual(resolved1, long_url)
        
        # Switch to Snowflake strategy
        self.shortener.set_strategy(SnowflakeShortener())
        short2 = self.shortener.shorten(long_url)
        resolved2 = self.shortener.resolve(short2)
        self.assertEqual(resolved2, long_url)
    
    def test_multiple_urls_same_db(self):
        """Test shortening multiple URLs with the same database."""
        urls = [
            "https://example.com/url1",
            "https://example.com/url2",
            "https://example.com/url3",
        ]
        
        shorts = [self.shortener.shorten(url) for url in urls]
        
        # Verify all shorts are unique
        self.assertEqual(len(shorts), len(set(shorts)))
        
        # Verify all resolve correctly
        for short, url in zip(shorts, urls):
            self.assertEqual(self.shortener.resolve(short), url)
    
    def test_strategy_isolation(self):
        """Test that different strategies have separate databases."""
        shortener1 = URLShortener(HashShortener())
        shortener2 = URLShortener(SnowflakeShortener())
        
        url = "https://example.com/test"
        short1 = shortener1.shorten(url)
        short2 = shortener2.shorten(url)
        
        # Different databases, so shorts should be different
        self.assertNotEqual(short1, short2)


class TestIntegration(unittest.TestCase):
    """Integration tests for the entire system."""
    
    def test_full_workflow_hash(self):
        """Test complete workflow with Hash strategy."""
        shortener = URLShortener(HashShortener())
        
        urls = [
            "https://github.com/tberhanu/URL-Shorteners",
            "https://example.com/very/long/url/path",
            "https://twitter.com/search?q=python",
        ]
        
        mapping = {}
        for url in urls:
            short = shortener.shorten(url)
            mapping[short] = url
        
        # Verify all mappings work
        for short, original in mapping.items():
            resolved = shortener.resolve(short)
            self.assertEqual(resolved, original)
    
    def test_full_workflow_snowflake(self):
        """Test complete workflow with Snowflake strategy."""
        shortener = URLShortener(SnowflakeShortener())
        
        urls = [
            "https://github.com/tberhanu/URL-Shorteners",
            "https://example.com/very/long/url/path",
            "https://twitter.com/search?q=python",
        ]
        
        mapping = {}
        for url in urls:
            short = shortener.shorten(url)
            mapping[short] = url
        
        # Verify all mappings work
        for short, original in mapping.items():
            resolved = shortener.resolve(short)
            self.assertEqual(resolved, original)
    
    def test_strategy_switch_workflow(self):
        """Test switching strategies in a workflow."""
        shortener = URLShortener(HashShortener())
        
        # Shorten with Hash
        hash_url = "https://example.com/hash"
        hash_short = shortener.shorten(hash_url)
        
        # Switch to Snowflake
        shortener.set_strategy(SnowflakeShortener())
        snowflake_url = "https://example.com/snowflake"
        snowflake_short = shortener.shorten(snowflake_url)
        
        # Both should still resolve (but from different strategies)
        self.assertEqual(shortener.resolve(hash_short), hash_url)
        self.assertEqual(shortener.resolve(snowflake_short), snowflake_url)


if __name__ == "__main__":
    unittest.main()
