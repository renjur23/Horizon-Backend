from django.utils.cache import add_never_cache_headers

class DisableClientCacheMiddleware:
    """
    Middleware to disable client/browser caching.
    Ideal for local development to always fetch fresh content.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        return response
