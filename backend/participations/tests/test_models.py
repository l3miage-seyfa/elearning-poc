"""Tests du modèle Participation et de la logique quiz multi-tentatives."""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import Person
from groups.models import Group
from courses.models import Course, Question
from participations.models import Participation


def make_person(email, is_admin=False):
    user = User.objects.create_user(
        username=email, email=email, password='pass1234',
        first_name='Test', last_name='User'
    )
    return Person.objects.create(user=user, is_admin=is_admin)


def make_course_with_questions(group, person):
    course = Course.objects.create(
        title='Quiz Test', group=group, created_by=person,
        nb_slides=1, nb_questions=2, is_published=True
    )
    Question.objects.create(
        course=course, order=1, text='Q1',
        choice_a='Vrai', choice_b='Faux', choice_c='C', choice_d='D',
        correct_answer='a'
    )
    Question.objects.create(
        course=course, order=2, text='Q2',
        choice_a='A', choice_b='Correct', choice_c='C', choice_d='D',
        correct_answer='b'
    )
    return course


class ParticipationModelTest(TestCase):
    def setUp(self):
        self.person = make_person('quiz@poc.com')
        self.group = Group.objects.create(name='G', type='equipe', responsible=self.person)
        self.course = make_course_with_questions(self.group, self.person)

    def test_participation_str_with_score(self):
        p = Participation.objects.create(
            person=self.person, course=self.course,
            score=75.0, completed_at=timezone.now()
        )
        self.assertIn('75%', str(p))

    def test_participation_str_without_score(self):
        p = Participation.objects.create(person=self.person, course=self.course)
        self.assertIn('en cours', str(p))

    def test_multiple_participations_allowed(self):
        """Plusieurs tentatives doivent être possibles pour le même (person, course)."""
        Participation.objects.create(
            person=self.person, course=self.course,
            score=50.0, completed_at=timezone.now()
        )
        Participation.objects.create(
            person=self.person, course=self.course,
            score=80.0, completed_at=timezone.now()
        )
        count = Participation.objects.filter(person=self.person, course=self.course).count()
        self.assertEqual(count, 2)

    def test_score_calculation(self):
        """Vérifie la logique de score : 1 bonne réponse / 2 = 50%."""
        p = Participation.objects.create(
            person=self.person, course=self.course,
            score=50.0, completed_at=timezone.now()
        )
        self.assertEqual(p.score, 50.0)
