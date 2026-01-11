import hashlib
import zlib


class SimpleBloomFilter:
    """
    A probabilistic data structure for fast existence checks.
    Uses three independent hash functions to minimize false positives.
    """
    
    def __init__(self, size=10000):
        self.size = size
        self.bit_array = [0] * size

    def _hashes(self, value):
        """
        Generate three independent hash values for the same input.
        
        Returns:
            List of three hash indices
        """
        return [
            hash(value) % self.size,
            zlib.crc32(value.encode()) % self.size,
            int(hashlib.md5(value.encode()).hexdigest(), 16) % self.size
        ]

    def add(self, value):
        """Add a value to the Bloom filter by setting three bit positions."""
        for h in self._hashes(value):
            self.bit_array[h] = 1

    def contains(self, value):
        """Check if a value might exist in the Bloom filter."""
        return all(self.bit_array[h] == 1 for h in self._hashes(value))
