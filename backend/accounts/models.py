from django.db import models
from django.contrib.auth.models import User


class Person(models.Model):
    """Profil utilisateur lié au User Django (auth)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='person')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.email})"

    class Meta:
        verbose_name = "Personne"
        verbose_name_plural = "Personnes"
