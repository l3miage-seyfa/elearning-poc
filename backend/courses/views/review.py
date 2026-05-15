from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from services.decorators import login_and_person_required
from courses.models import Course, Slide, Question


def _can_edit_course(person, course):
    """Vérifie si la personne a le droit d'éditer ce cours."""
    return (
        person.is_admin
        or course.created_by == person
        or course.group.responsible == person
    )


@login_and_person_required
def review_slides(request, pk):
    """Review + édition de toutes les slides avant publication."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        raise Http404

    slides = list(course.slides.order_by('order'))

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        with transaction.atomic():
            for slide in slides:
                new_content = request.POST.get(f'slide_{slide.pk}', '').strip()
                if new_content != slide.content:
                    slide.content = new_content
                    slide.save()
        if action == 'publish':
            course.is_published = True
            course.save()
            messages.success(request, f"Slides sauvegardées et cours « {course.title} » publié.")
            return redirect('courses:responsible_group', pk=course.group.pk)
        messages.success(request, "Slides sauvegardées.")
        return redirect('courses:review_slides', pk=course.pk)

    return render(request, 'courses/review/review_slides.html', {
        'course': course, 'slides': slides
    })


@login_and_person_required
def review_questions(request, pk):
    """Review + édition de toutes les questions avant publication."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        raise Http404

    questions = list(course.questions.order_by('order'))

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        with transaction.atomic():
            for q in questions:
                q.text           = request.POST.get(f'q_{q.pk}_text', '').strip()
                q.choice_a       = request.POST.get(f'q_{q.pk}_a', '').strip()
                q.choice_b       = request.POST.get(f'q_{q.pk}_b', '').strip()
                q.choice_c       = request.POST.get(f'q_{q.pk}_c', '').strip()
                q.choice_d       = request.POST.get(f'q_{q.pk}_d', '').strip()
                q.correct_answer = request.POST.get(f'q_{q.pk}_correct', 'a')
                q.explanation    = request.POST.get(f'q_{q.pk}_explanation', '').strip()
                q.save()
        if action == 'publish':
            course.is_published = True
            course.save()
            messages.success(request, f"Questions sauvegardées et cours « {course.title} » publié.")
            return redirect('courses:responsible_group', pk=course.group.pk)
        messages.success(request, "Questions sauvegardées.")
        return redirect('courses:review_questions', pk=course.pk)

    return render(request, 'courses/review/review_questions.html', {
        'course': course, 'questions': questions
    })


@login_and_person_required
def preview_questions(request, pk):
    """Aperçu lecture seule des questions (non interactif)."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        raise Http404
    questions = list(course.questions.order_by('order'))
    for q in questions:
        q.choices_display = [
            ('a', q.choice_a), ('b', q.choice_b),
            ('c', q.choice_c), ('d', q.choice_d),
        ]
    return render(request, 'courses/review/preview_questions.html', {
        'course': course, 'questions': questions
    })


@login_and_person_required
def course_publish(request, pk):
    """Publie (ou dépublie) un cours."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        raise Http404
    if request.method == 'POST':
        course.is_published = not course.is_published
        course.save()
        status = "publié" if course.is_published else "dépublié"
        messages.success(request, f"Cours « {course.title} » {status}.")
    return redirect('courses:responsible_group', pk=course.group.pk)


@login_and_person_required
def course_delete(request, pk):
    """Supprime un cours (responsable ou admin uniquement)."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        raise Http404
    if request.method == 'POST':
        title    = course.title
        group_id = course.group_id
        course.delete()
        messages.success(request, f"Cours « {title} » supprimé.")
        if person.is_admin:
            return redirect('courses:admin_dashboard')
        return redirect('courses:responsible_group', pk=group_id)
    return render(request, 'courses/group/course_confirm_delete.html', {'course': course})
