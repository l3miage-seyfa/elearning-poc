from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from services.decorators import login_and_person_required
from courses.models import Course, Question
from .models import Participation


@login_and_person_required
def take_quiz(request, course_pk):
    """Affiche les questions du quiz et traite la soumission."""
    course = get_object_or_404(Course, pk=course_pk, is_published=True)
    person = request.user.person

    # Vérifie si déjà participé
    existing = Participation.objects.filter(person=person, course=course).first()
    if existing and existing.score is not None:
        return redirect('participations:result', pk=existing.pk)

    questions = list(course.questions.order_by('order'))

    if request.method == 'POST':
        correct = 0
        for q in questions:
            answer = request.POST.get(f'q{q.pk}')
            if answer == q.correct_answer:
                correct += 1

        score = (correct / len(questions) * 100) if questions else 0
        participation, _ = Participation.objects.get_or_create(person=person, course=course)
        participation.score = round(score, 1)
        participation.completed_at = timezone.now()
        participation.save()
        return redirect('participations:result', pk=participation.pk)

    return render(request, 'participations/quiz.html', {
        'course': course,
        'questions': questions,
    })


@login_and_person_required
def result(request, pk):
    """Affiche le résultat d'une participation."""
    person = request.user.person
    participation = get_object_or_404(Participation, pk=pk, person=person)
    return render(request, 'participations/result.html', {'participation': participation})

