from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        # Django authentifie par username ; on cherche par email
        from django.contrib.auth.models import User
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
        messages.warning(request, "Votre compte n'a pas de profil Person.")
        return render(request, 'accounts/dashboard.html', {'person': None})

    if person.is_admin:
        return redirect('courses:admin_dashboard')

    return redirect('courses:member_courses')

