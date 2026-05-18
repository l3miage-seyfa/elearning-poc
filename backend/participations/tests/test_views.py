"""Tests des vues participations : slide_reader, take_quiz, result_detail, my_history."""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from accounts.models import Person
from groups.models import Group, GroupFile
from courses.models import Course, Slide, Question
from participations.models import Participation


def make_person(email, is_admin=False):
    user = User.objects.create_user(
        username=email, email=email, password='pass1234',
        first_name='Test', last_name='User'
    )
    return Person.objects.create(user=user, is_admin=is_admin)


def setup_course(group, person, published=True):
    course = Course.objects.create(
        title='Mon Cours', group=group, created_by=person,
        nb_slides=2, nb_questions=2, is_published=published
    )
    Slide.objects.create(course=course, order=1, content='# Slide 1\nContenu')
    Slide.objects.create(course=course, order=2, content='# Slide 2\nContenu')
    q1 = Question.objects.create(
        course=course, order=1, text='Question 1',
        choice_a='Vrai', choice_b='Faux', choice_c='C', choice_d='D',
        correct_answer='a'
    )
    q2 = Question.objects.create(
        course=course, order=2, text='Question 2',
        choice_a='A', choice_b='Bonne', choice_c='C', choice_d='D',
        correct_answer='b'
    )
    return course, q1, q2


class SlideReaderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = make_person('reader@poc.com')
        self.group = Group.objects.create(name='G', type='equipe', responsible=self.person)
        self.course, _, _ = setup_course(self.group, self.person)

    def test_slide_reader_first_slide(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:slide_reader', kwargs={'course_pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Slide 1')

    def test_slide_reader_second_slide(self):
        self.client.force_login(self.person.user)
        r = self.client.get(
            reverse('participations:slide_reader', kwargs={'course_pk': self.course.pk}),
            {'slide': 2}
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Slide 2')

    def test_slide_reader_requires_login(self):
        r = self.client.get(reverse('participations:slide_reader', kwargs={'course_pk': self.course.pk}))
        self.assertNotEqual(r.status_code, 200)

    def test_unpublished_course_not_accessible(self):
        self.course.is_published = False
        self.course.save()
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:slide_reader', kwargs={'course_pk': self.course.pk}))
        self.assertEqual(r.status_code, 404)


class TakeQuizTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = make_person('quizzer@poc.com')
        self.group = Group.objects.create(name='G2', type='equipe', responsible=self.person)
        self.course, self.q1, self.q2 = setup_course(self.group, self.person)

    def test_quiz_page_get(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)

    def test_quiz_submission_perfect_score(self):
        self.client.force_login(self.person.user)
        r = self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'a', f'q{self.q2.pk}': 'b'}
        )
        self.assertIn(r.status_code, [200, 302])
        p = Participation.objects.filter(person=self.person, course=self.course).last()
        self.assertIsNotNone(p)
        self.assertEqual(p.score, 100.0)

    def test_quiz_submission_zero_score(self):
        self.client.force_login(self.person.user)
        self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'b', f'q{self.q2.pk}': 'a'}  # mauvaises réponses
        )
        p = Participation.objects.filter(person=self.person, course=self.course).last()
        self.assertEqual(p.score, 0.0)

    def test_multiple_attempts_create_new_participation(self):
        """Repasser le quiz doit créer une nouvelle Participation."""
        self.client.force_login(self.person.user)
        self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'a', f'q{self.q2.pk}': 'b'}
        )
        self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'a', f'q{self.q2.pk}': 'b'}
        )
        count = Participation.objects.filter(person=self.person, course=self.course).count()
        self.assertEqual(count, 2)

    def test_attempt_number_increments(self):
        """Le champ attempt doit s'incrémenter à chaque nouvelle tentative."""
        self.client.force_login(self.person.user)
        self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'a', f'q{self.q2.pk}': 'b'}
        )
        self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'a', f'q{self.q2.pk}': 'b'}
        )
        attempts = list(
            Participation.objects.filter(person=self.person, course=self.course)
            .order_by('attempt').values_list('attempt', flat=True)
        )
        self.assertEqual(attempts, [1, 2])

    def test_unpublished_course_returns_404(self):
        self.course.is_published = False
        self.course.save()
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}))
        self.assertEqual(r.status_code, 404)

    def test_answers_stored_in_json(self):
        self.client.force_login(self.person.user)
        self.client.post(
            reverse('participations:take_quiz', kwargs={'course_pk': self.course.pk}),
            {f'q{self.q1.pk}': 'a', f'q{self.q2.pk}': 'b'}
        )
        p = Participation.objects.filter(person=self.person, course=self.course).last()
        answers = json.loads(p.answers)
        self.assertEqual(answers.get(str(self.q1.pk)), 'a')
        self.assertEqual(answers.get(str(self.q2.pk)), 'b')


class ResultDetailTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = make_person('result@poc.com')
        self.group = Group.objects.create(name='G3', type='equipe', responsible=self.person)
        self.course, self.q1, self.q2 = setup_course(self.group, self.person)
        answers = json.dumps({str(self.q1.pk): 'a', str(self.q2.pk): 'b'})
        self.participation = Participation.objects.create(
            person=self.person, course=self.course,
            score=100.0, completed_at=timezone.now(), answers=answers
        )

    def test_result_detail_accessible(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:result_detail', kwargs={'pk': self.participation.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '100')

    def test_result_detail_not_accessible_by_other(self):
        other = make_person('other@poc.com')
        self.client.force_login(other.user)
        r = self.client.get(reverse('participations:result_detail', kwargs={'pk': self.participation.pk}))
        self.assertEqual(r.status_code, 404)


class MyHistoryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = make_person('hist@poc.com')
        self.group = Group.objects.create(name='G4', type='equipe', responsible=self.person)
        self.course, _, _ = setup_course(self.group, self.person)

    def test_history_empty(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:my_history'))
        self.assertEqual(r.status_code, 200)

    def test_history_requires_login(self):
        r = self.client.get(reverse('participations:my_history'))
        self.assertNotEqual(r.status_code, 200)
        self.assertIn('/connexion/', r['Location'])

    def test_history_shows_participations(self):
        Participation.objects.create(
            person=self.person, course=self.course,
            score=75.0, completed_at=timezone.now()
        )
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:my_history'))
        self.assertContains(r, 'Mon Cours')
        self.assertContains(r, '75')

    def test_history_attempt_numbers(self):
        """Vérifie que attempt_number est bien passé au template."""
        Participation.objects.create(
            person=self.person, course=self.course,
            score=50.0, completed_at=timezone.now(), attempt=1
        )
        Participation.objects.create(
            person=self.person, course=self.course,
            score=80.0, completed_at=timezone.now(), attempt=2
        )
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:my_history'))
        self.assertEqual(r.status_code, 200)
        # Les 2 tentatives doivent apparaître
        participations = r.context['participations']
        self.assertEqual(len(participations), 2)
        attempt_numbers = {p.attempt_number for p in participations}
        self.assertEqual(attempt_numbers, {1, 2})


class ResultRedirectTest(TestCase):
    """La vue `result` doit rediriger vers `result_detail`."""

    def setUp(self):
        self.client = Client()
        self.person = make_person('redir@poc.com')
        self.group = Group.objects.create(name='G5', type='equipe', responsible=self.person)
        self.course, self.q1, self.q2 = setup_course(self.group, self.person)
        import json
        answers = json.dumps({str(self.q1.pk): 'a', str(self.q2.pk): 'b'})
        self.participation = Participation.objects.create(
            person=self.person, course=self.course,
            score=100.0, completed_at=timezone.now(), answers=answers
        )

    def test_result_redirects_to_result_detail(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('participations:result', kwargs={'pk': self.participation.pk}))
        self.assertRedirects(
            r,
            reverse('participations:result_detail', kwargs={'pk': self.participation.pk}),
            fetch_redirect_response=False
        )


def _make_group_file(group, person, name='doc.pdf'):
    """Crée un GroupFile avec un contenu PDF minimal."""
    gf = GroupFile(group=group, name=name, uploaded_by=person)
    gf.file.save(f'{name}', ContentFile(b'%PDF-1.4 fake'), save=True)
    return gf


class SlideReaderSourceFilesTest(TestCase):
    """Vérifie que slide_reader expose uniquement les source_files du cours."""

    def setUp(self):
        self.client = Client()
        self.responsible = make_person('resp_sf@poc.com')
        self.student = make_person('student_sf@poc.com')
        self.admin = make_person('admin_sf@poc.com', is_admin=True)
        self.group = Group.objects.create(name='G-SF', type='equipe', responsible=self.responsible)
        # Deux fichiers dans le groupe
        self.gf1 = _make_group_file(self.group, self.responsible, 'source1.pdf')
        self.gf2 = _make_group_file(self.group, self.responsible, 'source2.pdf')
        self.gf_other = _make_group_file(self.group, self.responsible, 'autre.pdf')
        # Cours lié seulement à gf1 + gf2
        self.course = Course.objects.create(
            title='Cours SF', group=self.group, created_by=self.responsible,
            nb_slides=1, nb_questions=1, is_published=True
        )
        self.course.source_files.set([self.gf1, self.gf2])
        Slide.objects.create(course=self.course, order=1, content='# SF\nContenu')
        # Ajouter étudiant au groupe
        from groups.models import GroupMembership
        GroupMembership.objects.get_or_create(person=self.student, group=self.group)

    def tearDown(self):
        for gf in [self.gf1, self.gf2, self.gf_other]:
            try:
                gf.file.delete(save=False)
            except Exception:
                pass

    def _get_reader(self, person, preview=False):
        self.client.force_login(person.user)
        url = reverse('participations:slide_reader', kwargs={'course_pk': self.course.pk})
        params = {'preview': '1'} if preview else {}
        return self.client.get(url, params)

    def test_student_voit_seulement_source_files(self):
        r = self._get_reader(self.student)
        self.assertEqual(r.status_code, 200)
        group_files = list(r.context['group_files'])
        pks = {gf.pk for gf in group_files}
        self.assertIn(self.gf1.pk, pks)
        self.assertIn(self.gf2.pk, pks)
        self.assertNotIn(self.gf_other.pk, pks)

    def test_responsable_preview_voit_seulement_source_files(self):
        r = self._get_reader(self.responsible, preview=True)
        self.assertEqual(r.status_code, 200)
        group_files = list(r.context['group_files'])
        pks = {gf.pk for gf in group_files}
        self.assertIn(self.gf1.pk, pks)
        self.assertNotIn(self.gf_other.pk, pks)

    def test_admin_preview_voit_seulement_source_files(self):
        r = self._get_reader(self.admin, preview=True)
        self.assertEqual(r.status_code, 200)
        group_files = list(r.context['group_files'])
        pks = {gf.pk for gf in group_files}
        self.assertIn(self.gf1.pk, pks)
        self.assertNotIn(self.gf_other.pk, pks)

    def test_cours_sans_source_files_retourne_liste_vide(self):
        self.course.source_files.clear()
        r = self._get_reader(self.student)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.context['group_files']), [])

    def test_deux_cours_sources_differentes(self):
        """Un second cours avec uniquement gf_other ne doit pas voir gf1/gf2."""
        course2 = Course.objects.create(
            title='Cours SF2', group=self.group, created_by=self.responsible,
            nb_slides=1, nb_questions=1, is_published=True
        )
        course2.source_files.set([self.gf_other])
        Slide.objects.create(course=course2, order=1, content='# SF2\nContenu')

        self.client.force_login(self.student.user)
        url = reverse('participations:slide_reader', kwargs={'course_pk': course2.pk})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        pks = {gf.pk for gf in r.context['group_files']}
        self.assertIn(self.gf_other.pk, pks)
        self.assertNotIn(self.gf1.pk, pks)
        self.assertNotIn(self.gf2.pk, pks)
