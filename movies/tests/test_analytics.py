from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class AnalyticsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staff', password='pwd', is_staff=True)
        self.normal_user = User.objects.create_user(username='normal', password='pwd', is_staff=False)
        self.dashboard_url = reverse('movies:admin_dashboard')
        self.api_url = reverse('movies:analytics_api')

    def test_anonymous_redirect(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)

    def test_normal_user_redirect(self):
        self.client.login(username='normal', password='pwd')
        response = self.client.get(self.dashboard_url)
        # staff_member_required redirects non-staff logged in users to the login page as well, wait, or shows 302
        self.assertEqual(response.status_code, 302)

    def test_staff_access(self):
        self.client.login(username='staff', password='pwd')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_api_access(self):
        self.client.login(username='staff', password='pwd')
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('revenue', data['data'])
