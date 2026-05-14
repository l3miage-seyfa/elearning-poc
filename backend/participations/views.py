from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from services.decorators import login_and_person_required
from courses.models import Course, Question, Slide
from .models import Participation


@login_and_person_required
def take_quiz(request, course_pk):
    """Affiche les questions du quiz et traite la soumission. Chaque tentative crée une nouvelle Participation."""
    course = get_object_or_404(Course, pk=course_pk, is_published=True)
    person = request.user.person
    questions = list(course.questions.order_by('order'))

    if request.method == 'POST':
        answers = {}
        correct = 0
        for q in questions:
            answer = request.POST.get(f'q{q.pk}')
            answers[q.pk] = answer
            if answer == q.correct_answer:
                correct += 1

        score = (correct / len(questions) * 100) if questions else 0
        import json
        participation = Participation.objects.create(
            person=person,
            course=course,
            score=round(score, 1),
            completed_at=timezone.now(),
            answers=json.dumps(answers),
        )
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
    participations = list(Participation.objects.filter(
        person=person, score__isnull=False
    ).select_related('course__group').order_by('course_id', 'completed_at'))

    # Numérotation des tentatives par cours
    from collections import defaultdict
    counters = defaultdict(int)
    for p in participations:
        counters[p.course_id] += 1
        p.attempt_number = counters[p.course_id]

    # Tri final par date décroissante pour l'affichage
    participations.sort(key=lambda p: p.completed_at or p.pk, reverse=True)

    return render(request, 'participations/my_history.html', {'participations': participations})


@login_and_person_required
def slide_reader(request, course_pk):
    """Lecture des slides : navigation précédent / suivant."""
    is_preview = request.GET.get('preview') == '1'
    # back_mode: 'slides' (retour modifier slides) ou 'group' (retour page groupe)
    back_mode = request.GET.get('back', 'slides')
    if is_preview:
        # Mode aperçu responsable : cours pas forcément publié
        course = get_object_or_404(Course, pk=course_pk)
        person = request.user.person
        if not (person.is_admin or course.created_by == person
                or (hasattr(course.group, 'responsible') and course.group.responsible == person)):
            from django.http import Http404
            raise Http404
    else:
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
        'has_prev': index > 0,
        'has_next': index < len(slides) - 1,
        'next_index': index + 2,
        'prev_index_1': index,
        'is_preview': is_preview,
        'back_mode': back_mode,
    })

