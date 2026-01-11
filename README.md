# URL Shortener - Low Level Design

A production-ready URL shortening service demonstrating multiple algorithms and design patterns.

## Overview

This implementation showcases two URL shortening strategies:
1. **Hash-based Shortener** - Uses cryptographic hashing with collision handling
2. **Snowflake + Base62 Shortener** - Uses distributed ID generation with base62 encoding

## Architecture

### Core Components

#### 1. **Bloom Filter** (`SimpleBloomFilter`)
- Probabilistic data structure for fast existence checks
- Uses three independent hash functions (built-in hash, CRC32, MD5)
- Eliminates false negatives with configurable bit array size
- Time: O(k) where k = number of hash functions
- Space: O(1) per lookup

#### 2. **In-Memory Database** (`InMemoryDB`)
- Stores short → long URL mappings
- Uses Bloom filter for fast existence checks before collision handling
- Methods:
  - `save(short_url, long_url)` - Store mapping
  - `get(short_url)` - Retrieve original URL
  - `exists(short_url)` - Check if short URL exists

#### 3. **Snowflake ID Generator**
- Generates unique distributed IDs with 69+ year collision-free guarantee
- Structure: `timestamp (milliseconds) << 12 | sequence number`
- Thread-safe using locks
- Sequence resets when timestamp changes

#### 4. **Base62 Encoding**
- Converts numeric IDs to compact alphanumeric strings
- Character set: `0-9a-zA-Z` (62 characters)
- More URL-friendly than hexadecimal

### Shortening Strategies

#### Hash-Based Strategy
```
Input: Long URL
  ↓
Generate hash (MD5/SHA1/CRC32)
  ↓
Take first 7 characters
  ↓
Check Bloom filter for collision
  ↓ (if collision)
Append "unique" and rehash
  ↓
Store in DB and return short URL
```

**Pros:**
- Works with any URL
- Same URL always produces same short code

**Cons:**
- Collision handling adds complexity
- Hash length somewhat arbitrary

#### Snowflake + Base62 Strategy
```
Input: Long URL
  ↓
Generate Snowflake ID (guaranteed unique)
  ↓
Encode to base62
  ↓
Store in DB and return short URL
```

**Pros:**
- No collision handling needed (69+ year guarantee)
- Shorter codes than hashing
- Deterministic and ordered
- Better for distributed systems

**Cons:**
- Different URL = different short code (even if duplicate)

## Design Patterns

### Strategy Pattern
- `ShorteningStrategy` interface defines algorithm contract
- Multiple implementations can be switched at runtime
- `URLShortener` context accepts any strategy

Example:
```python
shortener = URLShortener(HashShortener(method="md5"))
shortener.set_strategy(SnowflakeShortener())  # Switch at runtime
```

## Performance Characteristics

| Operation | Time | Space |
|-----------|------|-------|
| Shorten (Snowflake) | O(log n) | O(1) per ID |
| Shorten (Hash) | O(1) avg, O(k) worst | O(1) |
| Resolve | O(1) | - |
| Exists check | O(k) | - |

*k = collision retry count (rare for Snowflake)*

## Collision Analysis

### Snowflake-Based
- ID space: 2^52 timestamps × 2^12 sequences = ~4.5 quadrillion unique IDs per millisecond
- Collision probability: ~0% for 69 years at high throughput
- **No collision handling needed**

### Hash-Based
- Uses Bloom filter for fast rejection
- Collision resolution through rehashing
- Success depends on hash function distribution

## Usage Example

```python
from snowflake_base62_shortener import URLShortener, HashShortener, SnowflakeShortener

# Create shortener with Hash strategy
shortener = URLShortener(HashShortener(method="md5"))

# Shorten URL
long_url = "https://example.com/some/very/long/url"
short = shortener.shorten(long_url)
print(f"Shortened: {short}")

# Resolve URL
resolved = shortener.resolve(short)
print(f"Resolved: {resolved}")

# Switch to Snowflake strategy
shortener.set_strategy(SnowflakeShortener())
short2 = shortener.shorten(long_url)
print(f"Snowflake shortened: {short2}")
```

## Key Decisions

1. **In-memory storage** - Demonstrates core logic without external DB dependency
2. **Bloom filter** - Shows fast probabilistic existence checks
3. **Thread-safe Snowflake** - Production-ready concurrent ID generation
4. **Base62 encoding** - Compact, URL-safe representation
5. **Strategy pattern** - Allows algorithm flexibility without code changes

## Future Enhancements

- [ ] Persistent storage (Redis, PostgreSQL)
- [ ] Horizontal scaling with distributed Snowflake generators
- [ ] Custom short URL support (vanity URLs)
- [ ] URL expiration and cleanup
- [ ] Analytics and click tracking
- [ ] Rate limiting and abuse prevention

---

## URL Shortener Requirements & Design Considerations

### System Requirements

**Scale & Growth:**
- 100 Million URLs generated daily
- 365 Billion URLs per 10 years
- Short URL length critical for usability

**Character Set:**
- Allowed characters: `0-9`, `a-z`, `A-Z` (62 possible characters)
- Base62 encoding provides good compression

### Minimum URL Length Calculation

With base62 encoding, calculate minimum short URL length:

$$\text{pow}(62, n) \geq 365 \text{ Billion}$$

$$62^7 = 3.5 \text{ Trillion}$$

**Result:** Minimum 7 characters needed for 10 years of growth

### HTTP Redirect Strategies

#### 301 Redirect (Permanent)
- Status: "Permanently Moved to the Long URL"
- Browser Behavior: Results are **cached by browsers**
- Subsequent Requests: Won't be sent to shortener service
- Best For: Reducing server load and bandwidth
- Trade-off: Limited click tracking and analytics

#### 302 Redirect (Temporary)
- Status: "Temporarily Moved to the Long URL"
- Browser Behavior: Results are **not cached by browsers**
- Subsequent Requests: Will be sent to shortener service for each access
- Best For: Click tracking, analytics, and monitoring user behavior
- Use Case: Understanding click rate and traffic sources
- Trade-off: Higher server load but better insights

### Algorithm Comparison

#### Algorithm 1: Hash + Collision Resolution

**Process:**
1. Hash the long URL using MD5, SHA1, or CRC32
2. Extract first 7 characters from hash
3. Check Bloom filter for existence
4. **If collision detected:**
   - Append additional string (e.g., "unique")
   - Rehash and extract first 7 characters again
   - Repeat until unique code found
5. Store mapping in database

**Characteristics:**
- Deterministic: Same URL always produces same short code
- Collision handling required due to hash distribution
- Overhead from potential rehashing on collisions
- Good for deduplication (same long URL = same short URL)

#### Algorithm 2: Base62 Conversion (Snowflake-based)

**Process:**
1. Generate unique number using ID generator (e.g., Twitter Snowflake)
2. Convert generated number to Base62 encoding
3. Store mapping directly (no collision checks needed)

**Characteristics:**
- Monotonically increasing IDs (grows with time)
- Size not fixed (varies based on ID magnitude)
- No collision handling required for 69+ years
- Ideal for distributed systems
- Better for high-throughput scenarios

**ID Generation Options:**
- Sequential counter: Simple but not suitable for distributed systems (security/predictability)
- Twitter Snowflake: Distributed, thread-safe, guaranteed unique IDs

### Decision Matrix

| Criteria | Hash-based | Snowflake-based |
|----------|-----------|-----------------|
| Deterministic | ✓ | ✗ |
| Collision Risk | High | None (69+ years) |
| Deduplication | ✓ | ✗ |
| Distributed Ready | ✗ | ✓ |
| URL Length | Fixed (7) | Variable |
| Complexity | Medium | Low |
| Performance | O(1) avg | O(1) |
