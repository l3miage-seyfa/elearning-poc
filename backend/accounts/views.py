from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from services.decorators import admin_required
from .models import Person


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('accounts:dashboard')
        messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    person = getattr(request.user, 'person', None)
    if person is None:
        if request.user.is_superuser:
            Person.objects.create(user=request.user, is_admin=True)
            return redirect('courses:admin_dashboard')
        messages.warning(request, "Votre compte n'a pas de profil Person.")
        logout(request)
        return redirect('accounts:login')

    if person.is_admin:
        return redirect('courses:admin_dashboard')

    return redirect('courses:member_courses')


# ─── CRUD Personnes (admin uniquement) ────────────────────────────────────────

@admin_required
def person_list(request):
    persons = Person.objects.select_related('user').order_by('user__last_name', 'user__first_name')
    return render(request, 'accounts/person_list.html', {'persons': persons})


@admin_required
def person_create(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        password   = request.POST.get('password', '')
        is_admin   = request.POST.get('is_admin') == 'on'

        errors = []
        if not first_name: errors.append("Le prénom est requis.")
        if not last_name:  errors.append("Le nom est requis.")
        if not email:      errors.append("L'email est requis.")
        if not password:   errors.append("Le mot de passe est requis.")
        if User.objects.filter(email=email).exists():
            errors.append("Cet email est déjà utilisé.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/person_form.html', {
                'action': 'Créer', 'values': request.POST
            })

        username = email.split('@')[0]
        base, i = username, 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{i}"; i += 1

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        Person.objects.create(user=user, is_admin=is_admin)
        messages.success(request, f"Personne « {user.get_full_name()} » créée.")
        return redirect('accounts:person_list')

    return render(request, 'accounts/person_form.html', {'action': 'Créer', 'values': {}})


@admin_required
def person_edit(request, pk):
    person = get_object_or_404(Person, pk=pk)
    user = person.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        new_email       = request.POST.get('email', '').strip().lower()
        is_admin        = request.POST.get('is_admin') == 'on'
        new_password    = request.POST.get('password', '').strip()

        if new_email != user.email and User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, 'accounts/person_form.html', {
                'action': 'Modifier', 'person': person, 'values': request.POST
            })

        user.email = new_email
        if new_password:
            user.set_password(new_password)
        user.save()
        person.is_admin = is_admin
        person.save()
        messages.success(request, f"Personne « {user.get_full_name()} » mise à jour.")
        return redirect('accounts:person_list')

    return render(request, 'accounts/person_form.html', {
        'action': 'Modifier', 'person': person,
        'values': {
            'first_name': user.first_name, 'last_name': user.last_name,
            'email': user.email, 'is_admin': person.is_admin,
        }
    })


@admin_required
def person_delete(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if person.user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('accounts:person_list')
    if request.method == 'POST':
        name = person.user.get_full_name()
        person.user.delete()  # cascade → supprime aussi Person
        messages.success(request, f"Personne « {name} » supprimée.")
        return redirect('accounts:person_list')
    return render(request, 'accounts/person_confirm_delete.html', {'person': person})

