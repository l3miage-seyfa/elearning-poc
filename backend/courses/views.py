import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from services.decorators import login_and_person_required, admin_required
from services.ai_service import extract_pdf_text, generate_slides, generate_questions
from services.storage_service import upload_pdf
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


@admin_required
def upload_pdf_view(request):
    """
    Upload un PDF → extrait le texte → génère slides + questions via GPT-4o.
    Si un course_id est passé en GET/POST, enrichit un cours existant.
    Sinon crée un nouveau cours.
    """
    groups = Group.objects.all()
    course_id = request.GET.get('course_id') or request.POST.get('course_id')
    existing_course = None
    if course_id:
        existing_course = get_object_or_404(Course, pk=course_id)

    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        title = request.POST.get('title', '').strip()
        group_id = request.POST.get('group')
        nb_slides = int(request.POST.get('nb_slides', 5))
        nb_questions = int(request.POST.get('nb_questions', 5))

        if not pdf_file:
            messages.error(request, "Veuillez sélectionner un fichier PDF.")
            return render(request, 'courses/upload_pdf.html', {
                'groups': groups, 'existing_course': existing_course
            })

        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, "Le fichier doit être un PDF.")
            return render(request, 'courses/upload_pdf.html', {
                'groups': groups, 'existing_course': existing_course
            })

        try:
            pdf_bytes = pdf_file.read()

            # 1. Extrait le texte
            pdf_text = extract_pdf_text(pdf_bytes)
            if not pdf_text.strip():
                messages.error(request, "Impossible d'extraire du texte de ce PDF (PDF scanné ?).")
                return render(request, 'courses/upload_pdf.html', {
                    'groups': groups, 'existing_course': existing_course
                })

            # 2. Upload vers le bucket (optionnel si pas configuré)
            pdf_key = ''
            try:
                safe_name = f"{uuid.uuid4().hex}_{pdf_file.name.replace(' ', '_')}"
                pdf_key = upload_pdf(pdf_bytes, safe_name)
            except Exception:
                # Le bucket n'est pas configuré en local — on continue sans
                pass

            # 3. Génère slides + questions via GPT-4o
            slides_data = generate_slides(pdf_text, nb_slides)
            questions_data = generate_questions(pdf_text, nb_questions)

            # 4. Sauvegarde en BDD (transaction atomique)
            with transaction.atomic():
                if existing_course:
                    course = existing_course
                    course.nb_slides = nb_slides
                    course.nb_questions = nb_questions
                    if pdf_key:
                        course.pdf_file = pdf_key
                    course.save()
                    # Recrée slides + questions
                    course.slides.all().delete()
                    course.questions.all().delete()
                else:
                    if not title or not group_id:
                        messages.error(request, "Titre et groupe requis pour un nouveau cours.")
                        return render(request, 'courses/upload_pdf.html', {
                            'groups': groups, 'existing_course': existing_course
                        })
                    course = Course.objects.create(
                        title=title,
                        group_id=group_id,
                        created_by=request.user.person,
                        nb_slides=nb_slides,
                        nb_questions=nb_questions,
                        pdf_file=pdf_key,
                    )

                Slide.objects.bulk_create([
                    Slide(course=course, order=s.get('order', i + 1), content=s.get('content', ''))
                    for i, s in enumerate(slides_data)
                ])

                Question.objects.bulk_create([
                    Question(
                        course=course,
                        order=q.get('order', i + 1),
                        text=q.get('text', ''),
                        choice_a=q.get('choice_a', ''),
                        choice_b=q.get('choice_b', ''),
                        choice_c=q.get('choice_c', ''),
                        choice_d=q.get('choice_d', ''),
                        correct_answer=q.get('correct_answer', 'a'),
                        explanation=q.get('explanation', ''),
                    )
                    for i, q in enumerate(questions_data)
                ])

                course.is_published = True
                course.save()

            messages.success(
                request,
                f"Cours « {course.title} » généré avec {len(slides_data)} slides "
                f"et {len(questions_data)} questions. Publié automatiquement."
            )
            return redirect('courses:course_detail', pk=course.pk)

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération : {e}")

    return render(request, 'courses/upload_pdf.html', {
        'groups': groups,
        'existing_course': existing_course,
    })


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

