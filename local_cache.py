"""
Local Caching Module
Saves fetched HTML files locally to avoid re-fetching during development
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Optional

class LocalCache:
    """Simple file-based cache for HTML files"""
    
    def __init__(self, cache_dir: str = './cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.html_dir = self.cache_dir / 'html'
        self.metadata_dir = self.cache_dir / 'metadata'
        self.html_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key from URL"""
        # Use MD5 hash of URL as filename
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_html(self, url: str) -> Optional[str]:
        """Get cached HTML if it exists"""
        cache_key = self._get_cache_key(url)
        cache_file = self.html_dir / f"{cache_key}.html"
        
        if cache_file.exists():
            print(f"    ✓ Loading from cache")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"    Error reading cache: {e}")
                return None
        
        return None
    
    def save_html(self, url: str, html_content: str, metadata: dict = None):
        """Save HTML to cache"""
        cache_key = self._get_cache_key(url)
        cache_file = self.html_dir / f"{cache_key}.html"
        meta_file = self.metadata_dir / f"{cache_key}.json"
        
        try:
            # Save HTML
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save metadata (URL, timestamp, etc.)
            meta = {
                'url': url,
                'cached_at': str(Path(cache_file).stat().st_mtime),
                'size': len(html_content),
                **(metadata or {})
            }
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
            
            print(f"    ✓ Saved to cache ({len(html_content):,} chars)")
            
        except Exception as e:
            print(f"    Warning: Could not save to cache: {e}")
    
    def clear_cache(self):
        """Clear all cached files"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            self.html_dir.mkdir(exist_ok=True)
            self.metadata_dir.mkdir(exist_ok=True)
            print("Cache cleared")
    
    def get_cache_info(self):
        """Get information about cached files"""
        html_files = list(self.html_dir.glob('*.html'))
        
        total_size = sum(f.stat().st_size for f in html_files)
        
        return {
            'num_files': len(html_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# Singleton instance
_cache = None

def get_cache() -> LocalCache:
    """Get the global cache instance"""
    global _cache
    if _cache is None:
        _cache = LocalCache()
    return _cache


if __name__ == "__main__":
    # Test the cache
    cache = LocalCache('./test_cache')
    
    # Test saving
    test_url = "https://example.com/test.html"
    test_html = "<html><body>Test content</body></html>"
    
    cache.save_html(test_url, test_html, {'test': True})
    
    # Test loading
    loaded = cache.get_html(test_url)
    
    if loaded == test_html:
        print("✓ Cache working correctly!")
    else:
        print("✗ Cache test failed")
    
    # Show info
    info = cache.get_cache_info()
    print(f"\nCache info: {info}")
    
    # Cleanup
    cache.clear_cache()
    print("Test cache cleaned up")
