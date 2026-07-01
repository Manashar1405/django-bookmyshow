from django.test import TestCase
from movies.models import Movie, Genre
from movies.services.facets import FacetService
from django.core.cache import cache

class FacetServiceTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.g = Genre.objects.create(name='Action', slug='action')
        self.m1 = Movie.objects.create(name='Movie 1', rating=8.0)
        self.m1.genres.add(self.g)

    def test_cache_hit_and_miss(self):
        qs = Movie.objects.all()
        
        # First call calculates and caches
        facets1 = FacetService.get_genre_facets(qs)
        self.assertEqual(facets1[0]['movie_count'], 1)
        
        # Manually alter DB to prove next call hits cache
        self.m2 = Movie.objects.create(name='Movie 2', rating=7.0)
        self.m2.genres.add(self.g)
        
        # Second call should hit cache and still return 1
        facets2 = FacetService.get_genre_facets(qs)
        self.assertEqual(facets2[0]['movie_count'], 1)
        
        # Clear cache and verify it updates
        cache.clear()
        facets3 = FacetService.get_genre_facets(qs)
        self.assertEqual(facets3[0]['movie_count'], 2)
