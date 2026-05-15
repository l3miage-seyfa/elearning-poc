from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from services.decorators import admin_required
from services.ai_service import extract_pdf_text, generate_slides, generate_questions
from groups.models import Group
from courses.models import Course, Slide, Question


@admin_required
def admin_dashboard(request):
    """Vue principale de l'admin : compteurs + liste des cours."""
    from accounts.models import Person
    from participations.models import Participation

    courses = Course.objects.select_related('group', 'created_by__user').order_by('-created_at')
    groups  = Group.objects.all()

    stats = {
        'nb_persons':        Person.objects.count(),
        'nb_groups':         Group.objects.count(),
        'nb_courses':        courses.count(),
        'nb_published':      courses.filter(is_published=True).count(),
        'nb_participations': Participation.objects.count(),
    }
    return render(request, 'courses/admin/admin_dashboard.html', {
        'courses': courses,
        'groups':  groups,
        'stats':   stats,
    })
