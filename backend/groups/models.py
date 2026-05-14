from django.db import models


class Group(models.Model):
    TYPE_CHOICES = [
        ('direction', 'Direction'),
        ('equipe', 'Équipe'),
        ('projet', 'Projet'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='equipe', verbose_name="Type")
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name="Groupe parent"
    )
    responsible = models.ForeignKey(
        'accounts.Person', on_delete=models.PROTECT,
        related_name='managed_groups',
        verbose_name="Responsable"
    )
    members = models.ManyToManyField(
        'accounts.Person',
        through='GroupMembership',
        related_name='groups',
        verbose_name="Membres"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        GroupMembership.objects.get_or_create(person=self.responsible, group=self)

    def get_ancestors(self):
        """Retourne la liste de tous les groupes ancêtres (du plus proche au plus loin)."""
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"


class GroupMembership(models.Model):
    person = models.ForeignKey('accounts.Person', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('person', 'group')
        verbose_name = "Appartenance au groupe"
        verbose_name_plural = "Appartenances aux groupes"

    def __str__(self):
        return f"{self.person} → {self.group}"
