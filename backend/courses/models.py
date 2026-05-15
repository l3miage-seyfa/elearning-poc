from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=300, verbose_name="Titre")
    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Groupe"
    )
    created_by = models.ForeignKey(
        'accounts.Person', on_delete=models.SET_NULL, null=True,
        related_name='created_courses',
        verbose_name="Créé par"
    )
    nb_slides = models.PositiveIntegerField(default=5, verbose_name="Nombre de slides souhaité")
    nb_questions = models.PositiveIntegerField(default=5, verbose_name="Nombre de questions souhaité")
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "✅" if self.is_published else "⏳"
        return f"{status} {self.title} ({self.group.name})"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['-created_at']
        unique_together = [('title', 'group')]


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
    ANSWER_CHOICES = [('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]

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
