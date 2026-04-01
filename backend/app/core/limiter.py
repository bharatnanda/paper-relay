try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ImportError:  # pragma: no cover - local fallback when dependency is absent
    Limiter = None
    get_remote_address = None


class NoOpLimiter:
    def limit(self, _value: str):
        def decorator(func):
            return func
        return decorator


limiter = Limiter(key_func=get_remote_address) if Limiter and get_remote_address else NoOpLimiter()
