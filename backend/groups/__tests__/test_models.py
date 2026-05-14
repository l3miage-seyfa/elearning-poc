"""Tests des modèles Group, GroupMembership, GroupFile."""
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Person
from groups.models import Group, GroupMembership, GroupFile


def make_person(email, is_admin=False):
    user = User.objects.create_user(
        username=email, email=email, password='pass1234',
        first_name='Test', last_name='User'
    )
    return Person.objects.create(user=user, is_admin=is_admin)


class GroupModelTest(TestCase):
    def setUp(self):
        self.resp = make_person('resp@poc.com')
        self.member = make_person('member@poc.com')
        self.group = Group.objects.create(
            name='Équipe Alpha', type='equipe', responsible=self.resp
        )

    def test_group_str(self):
        self.assertEqual(str(self.group), 'Équipe Alpha')

    def test_responsible_auto_added_as_member(self):
        """Le responsable doit être automatiquement ajouté comme membre."""
        self.assertTrue(
            GroupMembership.objects.filter(person=self.resp, group=self.group).exists()
        )

    def test_add_member(self):
        GroupMembership.objects.create(person=self.member, group=self.group)
        self.assertIn(self.member, self.group.members.all())

    def test_get_ancestors_flat(self):
        """Groupe sans parent → aucun ancêtre."""
        self.assertEqual(self.group.get_ancestors(), [])

    def test_get_ancestors_nested(self):
        parent = Group.objects.create(name='Direction', type='direction', responsible=self.resp)
        child = Group.objects.create(name='Sous-équipe', type='equipe', responsible=self.resp, parent=parent)
        ancestors = child.get_ancestors()
        self.assertIn(parent, ancestors)


class GroupHierarchyTest(TestCase):
    def setUp(self):
        self.resp = make_person('hier@poc.com')
        self.parent = Group.objects.create(name='Parent', type='direction', responsible=self.resp)
        self.child = Group.objects.create(name='Child', type='equipe', responsible=self.resp, parent=self.parent)
        self.grandchild = Group.objects.create(name='Grandchild', type='projet', responsible=self.resp, parent=self.child)

    def test_three_level_ancestors(self):
        ancestors = self.grandchild.get_ancestors()
        self.assertEqual(len(ancestors), 2)
        self.assertIn(self.parent, ancestors)
        self.assertIn(self.child, ancestors)
