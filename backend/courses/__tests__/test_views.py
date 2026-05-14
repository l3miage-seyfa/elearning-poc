"""Tests des vues courses : admin_dashboard, member_courses, review, publish, delete."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Person
from groups.models import Group, GroupMembership
from courses.models import Course, Slide, Question


def make_person(email, is_admin=False):
    user = User.objects.create_user(
        username=email, email=email, password='pass1234',
        first_name='Test', last_name='User'
    )
    return Person.objects.create(user=user, is_admin=is_admin)


def make_course(group, person, title='Cours Test', published=True):
    return Course.objects.create(
        title=title, group=group, created_by=person,
        nb_slides=2, nb_questions=2, is_published=published
    )


class AdminDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_person('admin@poc.com', is_admin=True)
        self.normal = make_person('normal@poc.com', is_admin=False)

    def test_admin_can_access(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('courses:admin_dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_normal_user_blocked(self):
        self.client.force_login(self.normal.user)
        r = self.client.get(reverse('courses:admin_dashboard'))
        self.assertNotEqual(r.status_code, 200)


class MemberCoursesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = make_person('member@poc.com')
        self.group = Group.objects.create(name='G', type='equipe', responsible=self.person)
        self.course = make_course(self.group, self.person, published=True)

    def test_member_sees_published_course(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('courses:member_courses'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Cours Test')

    def test_unpublished_course_not_visible(self):
        self.course.is_published = False
        self.course.save()
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('courses:member_courses'))
        self.assertNotContains(r, 'Cours Test')

    def test_course_from_ancestor_group_visible(self):
        """Un cours du groupe parent doit être visible pour les membres du groupe enfant."""
        parent = Group.objects.create(name='Parent', type='direction', responsible=self.person)
        child = Group.objects.create(name='Child', type='equipe', responsible=self.person, parent=parent)
        child_member = make_person('child_member@poc.com')
        GroupMembership.objects.create(person=child_member, group=child)
        parent_course = make_course(parent, self.person, title='Cours Parent', published=True)

        self.client.force_login(child_member.user)
        r = self.client.get(reverse('courses:member_courses'))
        self.assertContains(r, 'Cours Parent')


class CoursePublishDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_person('admin2@poc.com', is_admin=True)
        self.group = Group.objects.create(name='G2', type='equipe', responsible=self.admin)
        self.course = make_course(self.group, self.admin, published=False)
        # Ajouter des slides pour review
        Slide.objects.create(course=self.course, order=1, content='Slide 1')
        Slide.objects.create(course=self.course, order=2, content='Slide 2')

    def test_review_slides_accessible(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('courses:review_slides', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)

    def test_publish_course(self):
        self.client.force_login(self.admin.user)
        r = self.client.post(reverse('courses:course_publish', kwargs={'pk': self.course.pk}))
        self.assertIn(r.status_code, [200, 302])
        self.assertTrue(Course.objects.get(pk=self.course.pk).is_published)

    def test_delete_course(self):
        self.client.force_login(self.admin.user)
        pk = self.course.pk
        r = self.client.post(reverse('courses:course_delete', kwargs={'pk': self.course.pk}))
        self.assertIn(r.status_code, [200, 302])
        self.assertFalse(Course.objects.filter(pk=pk).exists())
