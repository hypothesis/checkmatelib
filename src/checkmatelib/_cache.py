from cachetools import TTLCache


class MultiTTLCache:
    def __init__(self, max_items=10000):
        self._caches = {}
        self._max_items = max_items

    def get(self, key):
        for cache in self._caches.values():
            item = cache.get(key)
            if item:
                return item

        return None

    def add(self, key, item, ttl):
        ttl = int(ttl)

        if ttl not in self._caches:
            self._caches[ttl] = TTLCache(maxsize=self._max_items, ttl=ttl)

        self._caches[ttl][key] = item

        return item
