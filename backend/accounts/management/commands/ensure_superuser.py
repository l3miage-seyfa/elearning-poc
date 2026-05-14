import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Person


class Command(BaseCommand):
    help = "Crée le superuser admin depuis les variables d'environnement DJANGO_SUPERUSER_* si absent."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin@connect-tech.sncf')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', username)
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not password:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_PASSWORD non défini — superuser ignoré.'
            ))
            return

        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" créé avec succès.'))
        else:
            updates = []
            if user.email != email:
                user.email = email
                updates.append('email')
            if not user.is_staff:
                user.is_staff = True
                updates.append('is_staff')
            if not user.is_superuser:
                user.is_superuser = True
                updates.append('is_superuser')
            if updates:
                user.save(update_fields=updates)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" existe déjà.'))

        person, created = Person.objects.get_or_create(user=user, defaults={'is_admin': True})
        if not person.is_admin:
            person.is_admin = True
            person.save(update_fields=['is_admin'])
        action = 'créé' if created else 'vérifié'
        self.stdout.write(self.style.SUCCESS(f'Profil Person admin {action} pour "{username}".'))
