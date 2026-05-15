"""Tests des vues groups : my_groups, responsible_group_detail, add/remove member, file upload."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Person
from groups.models import Group, GroupMembership


def make_person(email, is_admin=False):
    user = User.objects.create_user(
        username=email, email=email, password='pass1234',
        first_name='Test', last_name='User'
    )
    return Person.objects.create(user=user, is_admin=is_admin)


class MyGroupsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = make_person('user@poc.com')
        self.group = Group.objects.create(name='G1', type='equipe', responsible=self.person)

    def test_my_groups_requires_login(self):
        r = self.client.get(reverse('groups:my_groups'))
        self.assertNotEqual(r.status_code, 200)

    def test_my_groups_shows_group(self):
        self.client.force_login(self.person.user)
        r = self.client.get(reverse('groups:my_groups'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'G1')


class ResponsibleGroupViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.resp = make_person('resp@poc.com')
        self.other = make_person('other@poc.com')
        self.group = Group.objects.create(name='TestGroup', type='equipe', responsible=self.resp)

    def test_responsible_can_access(self):
        self.client.force_login(self.resp.user)
        r = self.client.get(reverse('courses:responsible_group', kwargs={'pk': self.group.pk}))
        self.assertEqual(r.status_code, 200)

    def test_non_responsible_cannot_access(self):
        self.client.force_login(self.other.user)
        r = self.client.get(reverse('courses:responsible_group', kwargs={'pk': self.group.pk}))
        self.assertNotEqual(r.status_code, 200)


class AddRemoveMemberTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.resp = make_person('resp2@poc.com')
        self.new_member = make_person('newmember@poc.com')
        self.group = Group.objects.create(name='G2', type='equipe', responsible=self.resp)

    def test_add_member_by_email(self):
        self.client.force_login(self.resp.user)
        r = self.client.post(
            reverse('courses:group_add_member', kwargs={'pk': self.group.pk}),
            {'email': 'newmember@poc.com'}
        )
        self.assertIn(r.status_code, [200, 302])
        self.assertTrue(
            GroupMembership.objects.filter(person=self.new_member, group=self.group).exists()
        )

    def test_remove_member(self):
        GroupMembership.objects.get_or_create(person=self.new_member, group=self.group)
        self.client.force_login(self.resp.user)
        r = self.client.post(
            reverse('courses:group_remove_member', kwargs={
                'pk': self.group.pk, 'person_pk': self.new_member.pk
            })
        )
        self.assertIn(r.status_code, [200, 302])
        self.assertFalse(
            GroupMembership.objects.filter(person=self.new_member, group=self.group).exists()
        )


class GroupAdminCRUDTest(TestCase):
    """Tests CRUD groupes via les vues admin (group_list, group_create, group_delete)."""

    def setUp(self):
        self.client = Client()
        self.admin = make_person('admin@poc.com', is_admin=True)
        self.member = make_person('member@poc.com', is_admin=False)

    def test_group_list_accessible_to_admin(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('groups:group_list'))
        self.assertEqual(r.status_code, 200)

    def test_group_list_forbidden_to_member(self):
        self.client.force_login(self.member.user)
        r = self.client.get(reverse('groups:group_list'))
        self.assertNotEqual(r.status_code, 200)

    def test_group_create(self):
        self.client.force_login(self.admin.user)
        r = self.client.post(reverse('groups:group_create'), {
            'name': 'Nouveau Groupe',
            'type': 'equipe',
            'responsible': self.admin.pk,
            'description': '',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Group.objects.filter(name='Nouveau Groupe').exists())

    def test_group_delete(self):
        self.client.force_login(self.admin.user)
        group = Group.objects.create(name='A supprimer', type='equipe', responsible=self.admin)
        pk = group.pk
        r = self.client.post(reverse('groups:group_delete', args=[pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Group.objects.filter(pk=pk).exists())


class GroupDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.resp = make_person('gdetail_resp@poc.com')
        self.other = make_person('gdetail_other@poc.com')
        self.group = Group.objects.create(name='DetailGroup', type='equipe', responsible=self.resp)

    def test_responsible_can_access_detail(self):
        self.client.force_login(self.resp.user)
        r = self.client.get(reverse('groups:group_detail', kwargs={'pk': self.group.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'DetailGroup')

    def test_non_responsible_cannot_access_detail(self):
        self.client.force_login(self.other.user)
        r = self.client.get(reverse('groups:group_detail', kwargs={'pk': self.group.pk}))
        self.assertNotEqual(r.status_code, 200)

    def test_admin_can_access_detail(self):
        admin = make_person('gdetail_admin@poc.com', is_admin=True)
        self.client.force_login(admin.user)
        r = self.client.get(reverse('groups:group_detail', kwargs={'pk': self.group.pk}))
        self.assertEqual(r.status_code, 200)


class GroupEditViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_person('gedit_admin@poc.com', is_admin=True)
        self.group = Group.objects.create(name='EditGroup', type='equipe', responsible=self.admin)

    def test_group_edit_get(self):
        self.client.force_login(self.admin.user)
        r = self.client.get(reverse('groups:group_edit', kwargs={'pk': self.group.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'EditGroup')

    def test_group_edit_post_updates_name(self):
        self.client.force_login(self.admin.user)
        r = self.client.post(
            reverse('groups:group_edit', kwargs={'pk': self.group.pk}),
            {
                'name': 'NouveauNom',
                'type': 'equipe',
                'responsible': self.admin.pk,
                'description': '',
                'members': [],
            }
        )
        self.assertIn(r.status_code, [200, 302])
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'NouveauNom')

    def test_non_admin_cannot_edit_group(self):
        other = make_person('gedit_other@poc.com', is_admin=False)
        self.client.force_login(other.user)
        r = self.client.get(reverse('groups:group_edit', kwargs={'pk': self.group.pk}))
        self.assertNotEqual(r.status_code, 200)
