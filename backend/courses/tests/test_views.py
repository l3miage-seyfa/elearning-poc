"""Tests des vues courses : admin_dashboard, member_courses, review, publish, delete, fichiers, autocomplete."""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from accounts.models import Person
from groups.models import Group, GroupMembership, GroupFile
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


class ReviewSlidesQuestionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_person('admin3@poc.com', is_admin=True)
        self.group = Group.objects.create(name='G3', type='equipe', responsible=self.admin)
        self.course = make_course(self.group, self.admin, published=False)
        Slide.objects.create(course=self.course, order=1, content='Slide original 1')
        Slide.objects.create(course=self.course, order=2, content='Slide original 2')
        from courses.models import Question
        self.q = Question.objects.create(
            course=self.course, order=1, text='Question ?',
            choice_a='A', choice_b='B', choice_c='C', choice_d='D', correct_answer='a'
        )

    def test_review_questions_accessible(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('courses:review_questions', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)

    def test_save_slides(self):
        self.client.force_login(self.admin.user)
        slides = list(self.course.slides.order_by('order'))
        data = {'action': 'save'}
        for s in slides:
            data[f'slide_{s.pk}'] = f'Contenu modifié {s.order}'
        self.client.post(reverse('courses:review_slides', kwargs={'pk': self.course.pk}), data)
        slides[0].refresh_from_db()
        self.assertEqual(slides[0].content, 'Contenu modifié 1')

    def test_save_questions(self):
        self.client.force_login(self.admin.user)
        data = {
            'action': 'save',
            f'q_{self.q.pk}_text': 'Nouvelle question ?',
            f'q_{self.q.pk}_a': 'Choix A',
            f'q_{self.q.pk}_b': 'Choix B',
            f'q_{self.q.pk}_c': 'Choix C',
            f'q_{self.q.pk}_d': 'Choix D',
            f'q_{self.q.pk}_correct': 'b',
        }
        self.client.post(reverse('courses:review_questions', kwargs={'pk': self.course.pk}), data)
        self.q.refresh_from_db()
        self.assertEqual(self.q.text, 'Nouvelle question ?')
        self.assertEqual(self.q.correct_answer, 'b')


class PreviewQuestionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_person('prev_admin@poc.com', is_admin=True)
        self.other = make_person('prev_other@poc.com')
        self.group = Group.objects.create(name='GP', type='equipe', responsible=self.admin)
        self.course = make_course(self.group, self.admin, published=False)
        self.q = Question.objects.create(
            course=self.course, order=1, text='Q ?',
            choice_a='A', choice_b='B', choice_c='C', choice_d='D', correct_answer='a'
        )

    def test_responsible_can_preview(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('courses:preview_questions', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)

    def test_non_responsible_blocked(self):
        self.client.force_login(self.other.user)
        r = self.client.get(reverse('courses:preview_questions', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 404)


class MemberAutocompleteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_person('ac_admin@poc.com', is_admin=True)
        self.target = make_person('autocomplete_target@poc.com')
        self.target.user.first_name = 'Autocomplete'
        self.target.user.last_name = 'Target'
        self.target.user.save()

    def test_autocomplete_returns_json(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('courses:member_autocomplete'), {'q': 'auto'})
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertIn('results', data)

    def test_autocomplete_short_query_returns_empty(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('courses:member_autocomplete'), {'q': 'x'})
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertEqual(data.get('results', []), [])

    def test_autocomplete_requires_login(self):
        r = self.client.get(reverse('courses:member_autocomplete'), {'q': 'auto'})
        self.assertNotEqual(r.status_code, 200)


class GroupFileViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.resp = make_person('file_resp@poc.com')
        self.other = make_person('file_other@poc.com')
        self.group = Group.objects.create(name='FileGroup', type='equipe', responsible=self.resp)
        # Crée un fichier test dans la DB pour les tests rename/delete/download
        self.fake_file = SimpleUploadedFile('test.txt', b'contenu test', content_type='text/plain')
        self.group_file = GroupFile.objects.create(
            group=self.group, name='fichier_test', file=self.fake_file, uploaded_by=self.resp
        )

    def tearDown(self):
        # Nettoie le fichier physique créé
        try:
            self.group_file.file.delete(save=False)
        except Exception:
            pass

    def test_upload_file(self):
        self.client.force_login(self.resp.user)
        upload = SimpleUploadedFile('upload.txt', b'data', content_type='text/plain')
        r = self.client.post(
            reverse('courses:group_file_upload', kwargs={'pk': self.group.pk}),
            {'name': 'mon_fichier', 'file': upload}
        )
        self.assertIn(r.status_code, [200, 302])
        self.assertTrue(GroupFile.objects.filter(group=self.group, name='mon_fichier').exists())
        # Nettoyage
        GroupFile.objects.filter(group=self.group, name='mon_fichier').first().file.delete(save=False)

    def test_rename_file(self):
        self.client.force_login(self.resp.user)
        r = self.client.post(
            reverse('courses:group_file_rename', kwargs={'pk': self.group.pk, 'file_pk': self.group_file.pk}),
            {'name': 'nouveau_nom'}
        )
        self.assertIn(r.status_code, [200, 302])
        self.group_file.refresh_from_db()
        self.assertEqual(self.group_file.name, 'nouveau_nom')

    def test_delete_file(self):
        extra_file = SimpleUploadedFile('del.txt', b'x', content_type='text/plain')
        gf = GroupFile.objects.create(
            group=self.group, name='a_supprimer', file=extra_file, uploaded_by=self.resp
        )
        self.client.force_login(self.resp.user)
        r = self.client.post(
            reverse('courses:group_file_delete', kwargs={'pk': self.group.pk, 'file_pk': gf.pk})
        )
        self.assertIn(r.status_code, [200, 302])
        self.assertFalse(GroupFile.objects.filter(pk=gf.pk).exists())

    def test_non_responsible_cannot_upload(self):
        self.client.force_login(self.other.user)
        upload = SimpleUploadedFile('x.txt', b'x', content_type='text/plain')
        r = self.client.post(
            reverse('courses:group_file_upload', kwargs={'pk': self.group.pk}),
            {'name': 'x', 'file': upload}
        )
        # Le décorateur @responsible_required redirige (302) ou lève 404 → pas 200
        self.assertNotEqual(r.status_code, 200)

    def test_download_file(self):
        self.client.force_login(self.resp.user)
        r = self.client.get(
            reverse('courses:group_file_download', kwargs={'pk': self.group.pk, 'file_pk': self.group_file.pk})
        )
        self.assertIn(r.status_code, [200, 302])


class ResponsibleGroupDescriptionPostTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.resp = make_person('desc_resp@poc.com')
        self.group = Group.objects.create(name='DescGroup', type='equipe', responsible=self.resp, description='')

    def test_post_update_description(self):
        self.client.force_login(self.resp.user)
        r = self.client.post(
            reverse('courses:responsible_group', kwargs={'pk': self.group.pk}),
            {'update_description': '1', 'description': 'Nouvelle description'}
        )
        self.assertIn(r.status_code, [200, 302])
        self.group.refresh_from_db()
        self.assertEqual(self.group.description, 'Nouvelle description')
