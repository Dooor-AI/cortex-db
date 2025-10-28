"""In-memory cache for API key authentication."""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from ..models.api_key import APIKey, APIKeyPermissions


@dataclass
class CachedAPIKey:
    """Cached API key data."""
    api_key: APIKey
    cached_at: float
    ttl: float = 300.0  # 5 minutes TTL


class APIKeyCache:
    """Simple in-memory cache for API keys."""
    
    def __init__(self):
        self._cache: Dict[str, CachedAPIKey] = {}
        self._cleanup_interval = 60.0  # Cleanup every minute
        self._last_cleanup = time.time()
    
    def get(self, key_hash: str) -> Optional[APIKey]:
        """Get API key from cache.
        
        Args:
            key_hash: SHA-256 hash of the API key
            
        Returns:
            APIKey if found and not expired, None otherwise
        """
        self._maybe_cleanup()
        
        cached = self._cache.get(key_hash)
        if not cached:
            return None
            
        # Check if expired
        if time.time() - cached.cached_at > cached.ttl:
            del self._cache[key_hash]
            return None
            
        return cached.api_key
    
    def set(self, key_hash: str, api_key: APIKey, ttl: float = 300.0) -> None:
        """Cache an API key.
        
        Args:
            key_hash: SHA-256 hash of the API key
            api_key: APIKey object to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self._cache[key_hash] = CachedAPIKey(
            api_key=api_key,
            cached_at=time.time(),
            ttl=ttl
        )
    
    def invalidate(self, key_hash: str) -> None:
        """Remove API key from cache.
        
        Args:
            key_hash: SHA-256 hash of the API key
        """
        self._cache.pop(key_hash, None)
    
    def invalidate_all(self) -> None:
        """Clear all cached API keys."""
        self._cache.clear()
    
    def _maybe_cleanup(self) -> None:
        """Clean up expired entries periodically."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
            
        self._last_cleanup = now
        expired_keys = []
        
        for key_hash, cached in self._cache.items():
            if now - cached.cached_at > cached.ttl:
                expired_keys.append(key_hash)
        
        for key_hash in expired_keys:
            del self._cache[key_hash]
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        self._maybe_cleanup()
        return {
            "cached_keys": len(self._cache),
            "total_requests": getattr(self, "_total_requests", 0),
            "cache_hits": getattr(self, "_cache_hits", 0),
            "cache_misses": getattr(self, "_cache_misses", 0),
        }


# Global cache instance
_api_key_cache = APIKeyCache()


def get_api_key_cache() -> APIKeyCache:
    """Get the global API key cache instance."""
    return _api_key_cache
