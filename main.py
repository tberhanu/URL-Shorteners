"""
URL Shortener - Low Level Design
Example usage demonstrating both Hash and Snowflake strategies.
"""

from url_shortener import URLShortener
from strategies import HashShortener, SnowflakeShortener


def main():
    """Demonstrate URL shortening with different strategies."""
    
    print("=" * 60)
    print("URL Shortener - Strategy Pattern Demo")
    print("=" * 60)
    
    # Example 1: Hash-based shortening
    print("\n[1] Hash-based Shortener (MD5)")
    print("-" * 60)
    shortener = URLShortener(HashShortener(method="md5"))
    
    long_url = "https://example.com/some/very/long/url"
    short = shortener.shorten(long_url)
    print(f"Original URL: {long_url}")
    print(f"Shortened:   {short}")
    print(f"Resolved:    {shortener.resolve(short)}")
    
    # Example 2: Hash with different input
    long_url2 = "https://github.com/tberhanu/URL-Shorteners"
    short2 = shortener.shorten(long_url2)
    print(f"\nOriginal URL: {long_url2}")
    print(f"Shortened:   {short2}")
    print(f"Resolved:    {shortener.resolve(short2)}")
    
    # Example 3: Switch to Snowflake strategy at runtime
    print("\n[2] Snowflake + Base62 Shortener")
    print("-" * 60)
    shortener.set_strategy(SnowflakeShortener())
    
    long_url3 = "https://example.com/some/very/long/url"
    short3 = shortener.shorten(long_url3)
    print(f"Original URL: {long_url3}")
    print(f"Shortened:   {short3}")
    print(f"Resolved:    {shortener.resolve(short3)}")
    
    # Example 4: Another Snowflake shortened URL
    long_url4 = "https://github.com/tberhanu/URL-Shorteners"
    short4 = shortener.shorten(long_url4)
    print(f"\nOriginal URL: {long_url4}")
    print(f"Shortened:   {short4}")
    print(f"Resolved:    {shortener.resolve(short4)}")
    
    print("\n" + "=" * 60)
    print("Strategy Pattern Benefits:")
    print("-" * 60)
    print("✓ Switch algorithms at runtime")
    print("✓ Add new strategies without modifying existing code")
    print("✓ Easy to test different implementations")
    print("✓ Clean separation of concerns")
    print("=" * 60)


if __name__ == "__main__":
    main()
