from flask_caching import Cache

# Initialize the cache object here with disabled caching
cache = Cache(config={'CACHE_TYPE': 'null'})  # Disable caching temporarily to ensure we're not using stale queries 