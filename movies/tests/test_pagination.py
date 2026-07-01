from django.test import TestCase, RequestFactory
from movies.models import Movie
from movies.services.pagination import PaginationService
from django.core.paginator import Page

class PaginationTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        for i in range(15):
            Movie.objects.create(name=f'Movie {i}', rating=5.0)

    def test_default_pagination(self):
        request = self.factory.get('/movies/')
        qs = Movie.objects.all().order_by('id')
        page_obj = PaginationService.get_paginated_page(qs, request, per_page=10)
        
        self.assertIsInstance(page_obj, Page)
        self.assertEqual(len(page_obj.object_list), 10)
        self.assertEqual(page_obj.number, 1)

    def test_second_page(self):
        request = self.factory.get('/movies/?page=2')
        qs = Movie.objects.all().order_by('id')
        page_obj = PaginationService.get_paginated_page(qs, request, per_page=10)
        
        self.assertEqual(len(page_obj.object_list), 5)
        self.assertEqual(page_obj.number, 2)

    def test_invalid_page_defaults_to_first(self):
        request = self.factory.get('/movies/?page=abc')
        qs = Movie.objects.all().order_by('id')
        page_obj = PaginationService.get_paginated_page(qs, request, per_page=10)
        
        self.assertEqual(page_obj.number, 1)

    def test_out_of_bounds_page_defaults_to_last(self):
        request = self.factory.get('/movies/?page=999')
        qs = Movie.objects.all().order_by('id')
        page_obj = PaginationService.get_paginated_page(qs, request, per_page=10)
        
        self.assertEqual(page_obj.number, 2)
