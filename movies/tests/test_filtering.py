from django.test import TestCase, RequestFactory
from django.db import connection
from django.test.utils import CaptureQueriesContext
from movies.models import Movie, Genre, Language, MovieSort
from movies.services.filtering import MovieFilterService
from movies.services.facets import FacetService
from django.http import QueryDict
import datetime

class FilterServiceTestCase(TestCase):
    def setUp(self):
        self.g_action = Genre.objects.create(name='Action', slug='action')
        self.g_comedy = Genre.objects.create(name='Comedy', slug='comedy')
        
        self.l_english = Language.objects.create(name='English', slug='english')
        self.l_hindi = Language.objects.create(name='Hindi', slug='hindi')

        self.m1 = Movie.objects.create(name='Action Movie', rating=8.0, release_date=datetime.date(2023, 1, 1))
        self.m1.genres.add(self.g_action)
        self.m1.languages.add(self.l_english)

        self.m2 = Movie.objects.create(name='Comedy Movie', rating=7.0, release_date=datetime.date(2023, 2, 1))
        self.m2.genres.add(self.g_comedy)
        self.m2.languages.add(self.l_hindi)

        self.m3 = Movie.objects.create(name='Action Comedy', rating=9.0, release_date=datetime.date(2023, 3, 1))
        self.m3.genres.add(self.g_action, self.g_comedy)
        self.m3.languages.add(self.l_english, self.l_hindi)

    def test_no_filters(self):
        qs = MovieFilterService.filter_queryset(QueryDict(''))
        self.assertEqual(qs.count(), 3)

    def test_single_genre_filter(self):
        qs = MovieFilterService.filter_queryset(QueryDict('genre=action'))
        self.assertEqual(qs.count(), 2)
        self.assertIn(self.m1, qs)
        self.assertIn(self.m3, qs)

    def test_multiple_genre_or_filter(self):
        qs = MovieFilterService.filter_queryset(QueryDict('genre=action&genre=comedy'))
        self.assertEqual(qs.count(), 3) # Should be an OR

    def test_genre_and_language_filter(self):
        # Action AND Hindi
        qs = MovieFilterService.filter_queryset(QueryDict('genre=action&language=hindi'))
        self.assertEqual(qs.count(), 1)
        self.assertIn(self.m3, qs)

    def test_invalid_slug_ignored(self):
        qs = MovieFilterService.filter_queryset(QueryDict('genre=invalid&genre=action'))
        self.assertEqual(qs.count(), 2) # Only processes 'action'

    def test_only_invalid_slug_empty_result(self):
        qs = MovieFilterService.filter_queryset(QueryDict('genre=invalid'))
        self.assertEqual(qs.count(), 0)

    def test_sorting_latest(self):
        qs = MovieFilterService.filter_queryset(QueryDict('sort=latest'))
        self.assertEqual(list(qs), [self.m3, self.m2, self.m1])

    def test_sorting_rating(self):
        qs = MovieFilterService.filter_queryset(QueryDict('sort=rating'))
        self.assertEqual(list(qs), [self.m3, self.m1, self.m2])

    def test_distinct_prevent_duplicates(self):
        qs = MovieFilterService.filter_queryset(QueryDict('genre=action&genre=comedy&language=english&language=hindi'))
        self.assertEqual(qs.count(), 3) # m3 shouldn't appear twice

    def test_facet_counting(self):
        # Filter for Hindi movies
        qs = MovieFilterService.filter_queryset(QueryDict('language=hindi'))
        facets = FacetService.get_genre_facets(qs)
        
        # Action should have 1, Comedy should have 2
        action_facet = next(f for f in facets if f['slug'] == 'action')
        comedy_facet = next(f for f in facets if f['slug'] == 'comedy')
        
        self.assertEqual(action_facet['movie_count'], 1)
        self.assertEqual(comedy_facet['movie_count'], 2)

    def test_n_plus_one_avoidance(self):
        # Even if we access genres and languages for every movie, query count should be stable
        qs = MovieFilterService.filter_queryset(QueryDict(''))
        
        with CaptureQueriesContext(connection) as ctx:
            for movie in qs:
                list(movie.genres.all())
                list(movie.languages.all())
                
        # 1 main query + 2 prefetch queries
        self.assertLessEqual(len(ctx.captured_queries), 3)
