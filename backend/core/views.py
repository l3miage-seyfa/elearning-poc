from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        # Django auth utilise username, on cherche par email
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou mot de passe incorrect.')
        except User.DoesNotExist:
            messages.error(request, 'Email ou mot de passe incorrect.')
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """Redirige vers le bon dashboard selon le rôle."""
    try:
        person = request.user.person
        if person.is_admin:
            return redirect('admin_dashboard')
        else:
            return redirect('member_courses')
    except Exception:
        return redirect('login')


@login_required
def admin_dashboard(request):
    from .models import Person, Group, Course
    context = {
        'nb_persons': Person.objects.count(),
        'nb_groups': Group.objects.count(),
        'nb_courses': Course.objects.filter(is_published=True).count(),
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def member_courses(request):
    from .models import Person, Group
    person = request.user.person
    # Récupérer tous les groupes de la personne + leurs ancêtres
    direct_groups = list(person.groups.all())
    all_groups = set(direct_groups)
    for g in direct_groups:
        for ancestor in g.get_ancestors():
            all_groups.add(ancestor)

    from .models import Course, Participation
    courses = Course.objects.filter(
        group__in=all_groups, is_published=True
    ).select_related('group').order_by('group__name', 'title')

    participations = {
        p.course_id: p.score
        for p in Participation.objects.filter(person=person)
    }

    context = {
        'courses': courses,
        'participations': participations,
    }
    return render(request, 'core/member_courses.html', context)
