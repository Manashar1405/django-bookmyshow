from django.db.models import Q, Count
from movies.models import Movie, MovieSort, Genre, Language

class MovieFilterService:
    @staticmethod
    def filter_queryset(query_params):
        queryset = Movie.objects.all().prefetch_related('genres', 'languages')
        
        # 1. Search Query
        search_query = query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(cast__icontains=search_query)
            )

        # 2. Genre Filters (OR within)
        genres = query_params.getlist('genre')
        if genres:
            # Validate slugs to ignore invalid ones safely
            valid_genre_slugs = list(Genre.objects.filter(slug__in=genres).values_list('slug', flat=True))
            if valid_genre_slugs:
                queryset = queryset.filter(genres__slug__in=valid_genre_slugs)
            elif genres: # If they provided genres but none are valid, return empty
                queryset = Movie.objects.none()

        # 3. Language Filters (OR within)
        languages = query_params.getlist('language')
        if languages:
            valid_lang_slugs = list(Language.objects.filter(slug__in=languages).values_list('slug', flat=True))
            if valid_lang_slugs:
                queryset = queryset.filter(languages__slug__in=valid_lang_slugs)
            elif languages:
                queryset = Movie.objects.none()

        # Ensure distinctness after M2M filtering
        if genres or languages:
            queryset = queryset.distinct()

        # 4. Sorting
        sort_param = query_params.get('sort', MovieSort.LATEST)
        
        # Validate sort_param against TextChoices
        if sort_param not in MovieSort.values:
            sort_param = MovieSort.LATEST

        if sort_param == MovieSort.LATEST:
            queryset = queryset.order_by('-release_date', '-id')
        elif sort_param == MovieSort.RATING:
            queryset = queryset.order_by('-rating', '-id')
        elif sort_param == MovieSort.TITLE:
            queryset = queryset.order_by('name', '-id')
        elif sort_param == MovieSort.POPULARITY:
            queryset = queryset.annotate(num_bookings=Count('booking')).order_by('-num_bookings', '-id')

        return queryset
