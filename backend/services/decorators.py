from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_and_person_required(view_func):
    """Vérifie que l'utilisateur est connecté et possède un profil Person."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'person'):
            messages.error(request, "Votre compte n'a pas de profil Person associé.")
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Réservé aux Person.is_admin = True."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'person') or not request.user.person.is_admin:
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def responsible_required(view_func):
    """Réservé aux responsables de groupe (Person is_admin OU responsable d'au moins 1 groupe)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        person = getattr(request.user, 'person', None)
        if person is None:
            return redirect('accounts:login')
        if not person.is_admin and not person.managed_groups.exists():
            messages.error(request, "Accès réservé aux responsables de groupe.")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
