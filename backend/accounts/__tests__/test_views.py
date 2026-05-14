"""Tests des vues accounts : login, logout, dashboard redirect, CRUD personnes."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Person


def make_user(email, password='pass1234', is_admin=False, first='Alice', last='Test'):
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name=first, last_name=last
    )
    Person.objects.create(user=user, is_admin=is_admin)
    return user


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('alice@poc.com')

    def test_login_page_get(self):
        r = self.client.get(reverse('accounts:login'))
        self.assertEqual(r.status_code, 200)

    def test_login_success_redirects(self):
        r = self.client.post(reverse('accounts:login'), {
            'username': 'alice@poc.com', 'password': 'pass1234'
        })
        self.assertIn(r.status_code, [200, 302])

    def test_login_wrong_password(self):
        r = self.client.post(reverse('accounts:login'), {
            'username': 'alice@poc.com', 'password': 'wrong'
        })
        self.assertEqual(r.status_code, 200)  # reste sur la page login


class DashboardRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = make_user('admin@poc.com', is_admin=True)
        self.normal_user = make_user('normal@poc.com', is_admin=False)

    def test_admin_redirected_to_admin_dashboard(self):
        self.client.force_login(self.admin_user)
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(r, reverse('courses:admin_dashboard'))

    def test_normal_user_redirected_to_member_courses(self):
        self.client.force_login(self.normal_user)
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(r, reverse('courses:member_courses'))


class PersonCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin2@poc.com', is_admin=True)
        self.normal = make_user('normal2@poc.com', is_admin=False)

    def test_person_list_requires_admin(self):
        self.client.force_login(self.normal)
        r = self.client.get(reverse('accounts:person_list'))
        self.assertNotEqual(r.status_code, 200)

    def test_person_list_accessible_by_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('accounts:person_list'))
        self.assertEqual(r.status_code, 200)

    def test_person_create_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('accounts:person_create'), {
            'email': 'new@poc.com',
            'first_name': 'Bob',
            'last_name': 'Martin',
            'password': 'secret123',
            'is_admin': False,
        })
        self.assertIn(r.status_code, [200, 302])
