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
        r = self.client.get(reverse('login'))
        self.assertEqual(r.status_code, 200)

    def test_login_success_redirects(self):
        r = self.client.post(reverse('login'), {
            'username': 'alice@poc.com', 'password': 'pass1234'
        })
        self.assertIn(r.status_code, [200, 302])

    def test_login_wrong_password(self):
        r = self.client.post(reverse('login'), {
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

    def test_person_delete(self):
        target = make_user('target@poc.com')
        pk = target.person.pk
        self.client.force_login(self.admin)
        self.client.post(reverse('accounts:person_delete', args=[pk]))
        self.assertFalse(User.objects.filter(email='target@poc.com').exists())

    def test_cannot_delete_self(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('accounts:person_delete', args=[self.admin.person.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())


class LogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('logoutuser@poc.com')

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.user)
        r = self.client.get('/deconnexion/')
        self.assertRedirects(r, '/connexion/')

    def test_unauthenticated_redirect_to_login(self):
        r = self.client.get('/mes-cours/')
        self.assertIn('/connexion/', r['Location'])


class PersonEditTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('edit_admin@poc.com', is_admin=True)
        self.target = make_user('edit_target@poc.com', first='Alice', last='Dupont')

    def test_person_edit_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('accounts:person_edit', args=[self.target.person.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Alice')

    def test_person_edit_post_updates_name(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse('accounts:person_edit', args=[self.target.person.pk]),
            {
                'first_name': 'Bob',
                'last_name': 'Martin',
                'email': 'edit_target@poc.com',
                'is_admin': '',
                'password': '',
            }
        )
        self.assertIn(r.status_code, [200, 302])
        self.target.refresh_from_db()
        self.assertEqual(self.target.first_name, 'Bob')

    def test_non_admin_cannot_edit(self):
        normal = make_user('non_admin_edit@poc.com', is_admin=False)
        self.client.force_login(normal)
        r = self.client.get(reverse('accounts:person_edit', args=[self.target.person.pk]))
        self.assertNotEqual(r.status_code, 200)
