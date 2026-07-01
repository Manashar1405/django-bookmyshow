from django.views.generic import TemplateView
from movies.services.filtering import MovieFilterService
from movies.services.facets import FacetService
from movies.services.pagination import PaginationService
from movies.models import MovieSort

class MovieListView(TemplateView):
    template_name = 'movies/movie_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Filter and sort movies
        filtered_movies = MovieFilterService.filter_queryset(self.request.GET)
        
        # 2. Get facets dynamically based on the filtered queryset
        genre_facets = FacetService.get_genre_facets(filtered_movies)
        language_facets = FacetService.get_language_facets(filtered_movies)
        
        # 3. Paginate
        page_obj = PaginationService.get_paginated_page(filtered_movies, self.request, per_page=12)
        
        # 4. Prepare active filters for UI badges
        active_genres = self.request.GET.getlist('genre')
        active_languages = self.request.GET.getlist('language')
        active_sort = self.request.GET.get('sort', MovieSort.LATEST)
        search_query = self.request.GET.get('q', '')

        context.update({
            'page_obj': page_obj,
            'genre_facets': genre_facets,
            'language_facets': language_facets,
            'active_genres': active_genres,
            'active_languages': active_languages,
            'active_sort': active_sort,
            'search_query': search_query,
            'MovieSort': MovieSort,
        })
        return context
