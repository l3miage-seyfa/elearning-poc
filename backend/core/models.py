from django.db import models
from django.contrib.auth.models import User


class Person(models.Model):
    """Utilisateur de l'application (lié au User Django pour l'auth)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='person')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.email})"

    class Meta:
        verbose_name = "Personne"
        verbose_name_plural = "Personnes"


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
        Person, on_delete=models.PROTECT,
        related_name='managed_groups',
        verbose_name="Responsable"
    )
    members = models.ManyToManyField(
        Person,
        through='GroupMembership',
        related_name='groups',
        verbose_name="Membres"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Le responsable est automatiquement membre du groupe
        GroupMembership.objects.get_or_create(person=self.responsible, group=self)

    def get_ancestors(self):
        """Retourne tous les groupes ancêtres (parents, grands-parents...)."""
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
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('person', 'group')
        verbose_name = "Appartenance au groupe"
        verbose_name_plural = "Appartenances aux groupes"


class Course(models.Model):
    title = models.CharField(max_length=300, verbose_name="Titre")
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Groupe"
    )
    created_by = models.ForeignKey(
        Person, on_delete=models.SET_NULL, null=True,
        related_name='created_courses',
        verbose_name="Créé par"
    )
    pdf_file = models.CharField(max_length=500, blank=True, verbose_name="Fichier PDF (clé storage)")
    nb_slides = models.PositiveIntegerField(default=5, verbose_name="Nombre de slides")
    nb_questions = models.PositiveIntegerField(default=5, verbose_name="Nombre de questions")
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "✅" if self.is_published else "⏳"
        return f"{status} {self.title} ({self.group.name})"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['-created_at']


class Slide(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='slides',
        verbose_name="Cours"
    )
    order = models.PositiveIntegerField(verbose_name="Ordre")
    content = models.TextField(verbose_name="Contenu")

    def __str__(self):
        return f"Slide {self.order} — {self.course.title}"

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ['order']


class Question(models.Model):
    ANSWER_CHOICES = [
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Cours"
    )
    order = models.PositiveIntegerField(verbose_name="Ordre")
    text = models.TextField(verbose_name="Question")
    choice_a = models.CharField(max_length=500, verbose_name="Choix A")
    choice_b = models.CharField(max_length=500, verbose_name="Choix B")
    choice_c = models.CharField(max_length=500, verbose_name="Choix C")
    choice_d = models.CharField(max_length=500, verbose_name="Choix D")
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES, verbose_name="Bonne réponse")
    explanation = models.TextField(blank=True, verbose_name="Explication")

    def __str__(self):
        return f"Q{self.order} — {self.course.title}"

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['order']


class Participation(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        related_name='participations',
        verbose_name="Personne"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='participations',
        verbose_name="Cours"
    )
    score = models.FloatField(verbose_name="Score (%)")
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person} — {self.course.title} : {self.score:.0f}%"

    class Meta:
        unique_together = ('person', 'course')
        verbose_name = "Participation"
        verbose_name_plural = "Participations"
