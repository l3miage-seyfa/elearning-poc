"""Tests des modèles Course, Slide, Question."""
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Person
from groups.models import Group
from courses.models import Course, Slide, Question


def make_person(email, is_admin=False):
    user = User.objects.create_user(
        username=email, email=email, password='pass1234',
        first_name='Test', last_name='User'
    )
    return Person.objects.create(user=user, is_admin=is_admin)


class CourseModelTest(TestCase):
    def setUp(self):
        self.person = make_person('creator@poc.com', is_admin=True)
        self.group = Group.objects.create(name='G', type='equipe', responsible=self.person)
        self.course = Course.objects.create(
            title='Intro RGPD', group=self.group,
            created_by=self.person, nb_slides=3, nb_questions=2,
            is_published=False
        )

    def test_course_str_unpublished(self):
        self.assertIn('⏳', str(self.course))
        self.assertIn('Intro RGPD', str(self.course))

    def test_course_str_published(self):
        self.course.is_published = True
        self.course.save()
        self.assertIn('✅', str(self.course))

    def test_course_default_not_published(self):
        self.assertFalse(self.course.is_published)

    def test_slides_ordered(self):
        Slide.objects.create(course=self.course, order=2, content='Slide 2')
        Slide.objects.create(course=self.course, order=1, content='Slide 1')
        slides = list(self.course.slides.all())
        self.assertEqual(slides[0].order, 1)
        self.assertEqual(slides[1].order, 2)

    def test_questions_ordered(self):
        Question.objects.create(
            course=self.course, order=2, text='Q2',
            choice_a='A', choice_b='B', choice_c='C', choice_d='D', correct_answer='a'
        )
        Question.objects.create(
            course=self.course, order=1, text='Q1',
            choice_a='A', choice_b='B', choice_c='C', choice_d='D', correct_answer='b'
        )
        questions = list(self.course.questions.all())
        self.assertEqual(questions[0].order, 1)


class CoursePublishDeleteTest(TestCase):
    def setUp(self):
        self.person = make_person('admin@poc.com', is_admin=True)
        self.group = Group.objects.create(name='G2', type='equipe', responsible=self.person)
        self.course = Course.objects.create(
            title='Test', group=self.group, created_by=self.person
        )

    def test_publish_course(self):
        self.course.is_published = True
        self.course.save()
        self.assertTrue(Course.objects.get(pk=self.course.pk).is_published)

    def test_delete_course(self):
        pk = self.course.pk
        self.course.delete()
        self.assertFalse(Course.objects.filter(pk=pk).exists())
