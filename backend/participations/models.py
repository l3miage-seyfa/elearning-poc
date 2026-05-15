from django.db import models


class Participation(models.Model):
    person = models.ForeignKey(
        'accounts.Person', on_delete=models.CASCADE,
        related_name='participations',
        verbose_name="Participant"
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='participations',
        verbose_name="Cours"
    )
    attempt = models.PositiveIntegerField(default=1, verbose_name="Tentative n°")
    score = models.FloatField(null=True, blank=True, verbose_name="Score (%)")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminé le")
    answers = models.TextField(blank=True, default='{}', verbose_name="Réponses (JSON)")

    def __str__(self):
        score_str = f"{self.score:.0f}%" if self.score is not None else "en cours"
        return f"{self.person} → {self.course.title} — tentative {self.attempt} ({score_str})"

    class Meta:
        verbose_name = "Participation"
        verbose_name_plural = "Participations"
        ordering = ['-completed_at']
