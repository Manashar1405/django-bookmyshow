import hashlib
from django.core.cache import cache
from django.db.models import Count, Q
from movies.models import Genre, Language

class FacetService:
    CACHE_VERSION = "v1"
    CACHE_TIMEOUT = 300  # 5 minutes

    @staticmethod
    def _generate_cache_key(prefix, queryset):
        # We hash the raw SQL query to create a unique cache key for these exact filter conditions
        sql, params = queryset.query.sql_with_params()
        query_hash = hashlib.md5(f"{sql}_{params}".encode('utf-8')).hexdigest()
        return f"movies:facets:{FacetService.CACHE_VERSION}:{prefix}:{query_hash}"

    @classmethod
    def get_genre_facets(cls, filtered_queryset):
        cache_key = cls._generate_cache_key("genre", filtered_queryset)
        facets = cache.get(cache_key)
        
        if facets is None:
            # Calculate how many of the *filtered* movies belong to each genre
            facets = list(Genre.objects.annotate(
                movie_count=Count('movies', filter=Q(movies__in=filtered_queryset))
            ).values('name', 'slug', 'movie_count').order_by('-movie_count', 'name'))
            cache.set(cache_key, facets, cls.CACHE_TIMEOUT)
            
        return facets

    @classmethod
    def get_language_facets(cls, filtered_queryset):
        cache_key = cls._generate_cache_key("language", filtered_queryset)
        facets = cache.get(cache_key)
        
        if facets is None:
            facets = list(Language.objects.annotate(
                movie_count=Count('movies', filter=Q(movies__in=filtered_queryset))
            ).values('name', 'slug', 'movie_count').order_by('-movie_count', 'name'))
            cache.set(cache_key, facets, cls.CACHE_TIMEOUT)
            
        return facets
