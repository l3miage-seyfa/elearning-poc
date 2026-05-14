"""Tests du modèle Person et de l'authentification."""
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Person


class PersonModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@poc.com', email='test@poc.com',
            password='testpass123', first_name='Alice', last_name='Dupont'
        )
        self.person = Person.objects.create(user=self.user, is_admin=False)

    def test_person_str(self):
        self.assertIn('Alice', str(self.person))

    def test_person_not_admin_by_default(self):
        self.assertFalse(self.person.is_admin)

    def test_admin_person(self):
        self.person.is_admin = True
        self.person.save()
        self.assertTrue(self.person.is_admin)
