from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from services.decorators import login_and_person_required, admin_required
from groups.models import Group
from .models import Course, Slide, Question


@admin_required
def admin_dashboard(request):
    """Vue principale de l'admin : liste tous les cours et groupes."""
    courses = Course.objects.select_related('group', 'created_by__user').order_by('-created_at')
    groups = Group.objects.all()
    return render(request, 'courses/admin_dashboard.html', {
        'courses': courses,
        'groups': groups,
    })


@login_and_person_required
def member_courses(request):
    """Vue membre : cours publiés accessibles via les groupes (et leurs ancêtres)."""
    person = request.user.person

    # Collecte tous les groupes dont l'user est membre + leurs ancêtres
    direct_groups = Group.objects.filter(members=person)
    all_group_ids = set()
    for group in direct_groups:
        all_group_ids.add(group.pk)
        for ancestor in group.get_ancestors():
            all_group_ids.add(ancestor.pk)

    courses = Course.objects.filter(
        is_published=True,
        group_id__in=all_group_ids
    ).select_related('group', 'created_by__user').order_by('-created_at')

    # Ajoute les participations existantes
    from participations.models import Participation
    participated_ids = set(
        Participation.objects.filter(person=person).values_list('course_id', flat=True)
    )

    return render(request, 'courses/member_courses.html', {
        'courses': courses,
        'participated_ids': participated_ids,
    })


@admin_required
def course_create(request):
    """Crée un cours manuellement (sans upload PDF, pour les tests)."""
    groups = Group.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        group_id = request.POST.get('group')
        nb_slides = int(request.POST.get('nb_slides', 5))
        nb_questions = int(request.POST.get('nb_questions', 5))
        if title and group_id:
            course = Course.objects.create(
                title=title,
                group_id=group_id,
                created_by=request.user.person,
                nb_slides=nb_slides,
                nb_questions=nb_questions,
            )
            messages.success(request, f"Cours « {course.title} » créé.")
            return redirect('courses:admin_dashboard')
        messages.error(request, "Titre et groupe requis.")
    return render(request, 'courses/course_form.html', {'groups': groups})


@login_and_person_required
def course_detail(request, pk):
    """Détail d'un cours : slides + questions."""
    course = get_object_or_404(Course, pk=pk, is_published=True)
    slides = course.slides.order_by('order')
    questions = course.questions.order_by('order')
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'slides': slides,
        'questions': questions,
    })

