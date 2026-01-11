import hashlib
import zlib
import time
import threading
import random
from abc import ABC, abstractmethod


# ============================================================
# In-memory DB + Bloom Filter Simulation
# ============================================================

class SimpleBloomFilter:
    def __init__(self, size=10000):
        self.size = size
        self.bit_array = [0] * size

    def _hashes(self, value):
        return [
            hash(value) % self.size,
            zlib.crc32(value.encode()) % self.size,
            int(hashlib.md5(value.encode()).hexdigest(), 16) % self.size
        ]

    def add(self, value):
        for h in self._hashes(value):
            self.bit_array[h] = 1

    def contains(self, value):
        return all(self.bit_array[h] == 1 for h in self._hashes(value))


class InMemoryDB:
    def __init__(self):
        self.map = {}  # short → long
        self.bloom = SimpleBloomFilter()

    def exists(self, short_url):
        return self.bloom.contains(short_url)

    def save(self, short_url, long_url):
        self.map[short_url] = long_url
        self.bloom.add(short_url)

    def get(self, short_url):
        return self.map.get(short_url, None)


# ============================================================
# Base62 Encoding
# ============================================================

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base62_encode(num):
    if num == 0:
        return "0"
    result = []
    while num > 0:
        num, rem = divmod(num, 62)
        result.append(BASE62[rem])
    return ''.join(reversed(result))


# ============================================================
# Snowflake ID Generator (Simplified)
# ============================================================

class Snowflake:
    def __init__(self):
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def _timestamp(self):
        return int(time.time() * 1000)

    def generate(self):
        with self.lock:
            timestamp = self._timestamp()

            if timestamp == self.last_timestamp:
                self.sequence += 1
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Combine timestamp + sequence
            return (timestamp << 12) | self.sequence


# ============================================================
# Strategy Interface
# ============================================================

class ShorteningStrategy(ABC):
    @abstractmethod
    def shorten(self, long_url, db: InMemoryDB):
        pass


# ============================================================
# Algorithm 1: Hash-based Shortener
# ============================================================

class HashShortener(ShorteningStrategy):
    def __init__(self, method="md5"):
        self.method = method

    def _hash(self, long_url):
        if self.method == "crc32":
            return format(zlib.crc32(long_url.encode()), "x")
        elif self.method == "sha1":
            return hashlib.sha1(long_url.encode()).hexdigest()
        else:
            return hashlib.md5(long_url.encode()).hexdigest()

    def shorten(self, long_url, db: InMemoryDB):
        hashed = self._hash(long_url)
        short = hashed[:7]

        # Ensure uniqueness
        while db.exists(short):
            short += "unique"
            short = hashlib.md5(short.encode()).hexdigest()[:7]

        db.save(short, long_url)
        return short


# ============================================================
# Algorithm 2: Snowflake + Base62 Shortener
# ============================================================

class SnowflakeShortener(ShorteningStrategy):
    def __init__(self):
        self.snowflake = Snowflake()

    def shorten(self, long_url, db: InMemoryDB):
        num = self.snowflake.generate()
        short = base62_encode(num)
        db.save(short, long_url)
        return short


# ============================================================
# Context Class (Strategy Pattern)
# ============================================================

class URLShortener:
    def __init__(self, strategy: ShorteningStrategy):
        self.strategy = strategy
        self.db = InMemoryDB()

    def set_strategy(self, strategy: ShorteningStrategy):
        self.strategy = strategy

    def shorten(self, long_url):
        return self.strategy.shorten(long_url, self.db)

    def resolve(self, short_url):
        return self.db.get(short_url)


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    # Choose strategy
    shortener = URLShortener(HashShortener(method="md5"))

    long_url = "https://example.com/some/very/long/url"

    short = shortener.shorten(long_url)
    print("Shortened:", short)
    print("Resolved:", shortener.resolve(short))

    # Switch strategy at runtime
    shortener.set_strategy(SnowflakeShortener())
    short2 = shortener.shorten(long_url)
    print("Shortened (Snowflake):", short2)
    print("Resolved:", shortener.resolve(short2))
