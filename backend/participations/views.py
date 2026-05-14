from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from services.decorators import login_and_person_required
from courses.models import Course, Question, Slide
from .models import Participation


@login_and_person_required
def take_quiz(request, course_pk):
    """Affiche les questions du quiz et traite la soumission."""
    course = get_object_or_404(Course, pk=course_pk, is_published=True)
    person = request.user.person

    # Vérifie si déjà participé
    existing = Participation.objects.filter(person=person, course=course).first()
    if existing and existing.score is not None:
        return redirect('participations:result_detail', pk=existing.pk)

    questions = list(course.questions.order_by('order'))

    if request.method == 'POST':
        answers = {}   # {question_pk: lettre_choisie}
        correct = 0
        for q in questions:
            answer = request.POST.get(f'q{q.pk}')
            answers[q.pk] = answer
            if answer == q.correct_answer:
                correct += 1

        score = (correct / len(questions) * 100) if questions else 0
        participation, _ = Participation.objects.get_or_create(person=person, course=course)
        participation.score = round(score, 1)
        participation.completed_at = timezone.now()
        # Stocke les réponses en JSON dans le champ answers
        import json
        participation.answers = json.dumps(answers)
        participation.save()
        return redirect('participations:result_detail', pk=participation.pk)

    return render(request, 'participations/quiz.html', {
        'course': course,
        'questions': questions,
    })


@login_and_person_required
def result(request, pk):
    """Redirige vers result_detail pour compatibilité."""
    return redirect('participations:result_detail', pk=pk)


@login_and_person_required
def result_detail(request, pk):
    """Résultats détaillés : pour chaque question, bonne/mauvaise réponse + explication."""
    import json
    person = request.user.person
    participation = get_object_or_404(Participation, pk=pk, person=person)
    questions = list(participation.course.questions.order_by('order'))

    try:
        answers = json.loads(participation.answers or '{}')
    except Exception:
        answers = {}

    # Construit une liste enrichie
    CHOICES = {'a': 'choice_a', 'b': 'choice_b', 'c': 'choice_c', 'd': 'choice_d'}
    results = []
    for q in questions:
        given = answers.get(str(q.pk))
        results.append({
            'question': q,
            'given': given,
            'given_text': getattr(q, CHOICES.get(given, ''), '') if given else None,
            'correct_text': getattr(q, CHOICES[q.correct_answer]),
            'is_correct': given == q.correct_answer,
        })

    return render(request, 'participations/result_detail.html', {
        'participation': participation,
        'results': results,
    })


@login_and_person_required
def my_history(request):
    """Historique complet des participations de la personne connectée."""
    person = request.user.person
    participations = Participation.objects.filter(
        person=person, score__isnull=False
    ).select_related('course__group').order_by('-completed_at')
    return render(request, 'participations/my_history.html', {'participations': participations})


@login_and_person_required
def slide_reader(request, course_pk):
    """Lecture des slides : navigation précédent / suivant."""
    course = get_object_or_404(Course, pk=course_pk, is_published=True)
    slides = list(course.slides.order_by('order'))
    try:
        index = int(request.GET.get('slide', 1)) - 1
    except ValueError:
        index = 0
    index = max(0, min(index, len(slides) - 1))
    slide = slides[index] if slides else None
    return render(request, 'participations/slide_reader.html', {
        'course': course,
        'slides': slides,
        'slide': slide,
        'index': index,
        'total': len(slides),
        'prev_index': index,        # 1-based dans le template
        'has_prev': index > 0,
        'has_next': index < len(slides) - 1,
        'next_index': index + 2,    # 1-based
        'prev_index_1': index,      # 1-based
    })

