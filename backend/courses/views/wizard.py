import io
import openai
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.files.base import ContentFile
from services.decorators import responsible_required
from services.ai_service import extract_pdf_text, generate_slides, generate_questions
from groups.models import Group, GroupFile
from courses.models import Course, Slide, Question


def _unique_title(base: str, group) -> str:
    """Retourne un titre unique dans le groupe en ajoutant un suffixe numérique si nécessaire."""
    title = base
    n = 2
    while Course.objects.filter(title=title, group=group).exists():
        title = f"{base} {n}"
        n += 1
    return title


@responsible_required
def course_create_wizard(request, pk):
    """
    Wizard création de cours pour un groupe.
    Choisir un fichier existant OU uploader un nouveau,
    saisir titre/nb_slides/nb_questions, puis générer avec GPT-4o.
    """
    from groups.models import GroupFile
    group  = get_object_or_404(Group, pk=pk)
    person = request.user.person
    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    group_files = group.files.order_by('-uploaded_at')

    if request.method == 'POST':
        title        = request.POST.get('title', '').strip()
        nb_slides    = int(request.POST.get('nb_slides', 5))
        nb_questions = int(request.POST.get('nb_questions', 5))

        # ── Fichiers existants cochés ────────────────────────────────────────
        existing_ids     = request.POST.getlist('file_ids[]')
        # ── Nouveaux fichiers uploadés + cochés ──────────────────────────────
        selected_uids    = request.POST.getlist('new_file_selected[]')
        new_files_all    = request.FILES.getlist('new_file[]')
        new_names_all    = request.POST.getlist('new_file_name[]')

        all_pdf_bytes: list[bytes] = []
        file_name = ''

        # 1) Fichiers existants
        for fid in existing_ids[:3]:
            gf = get_object_or_404(GroupFile, pk=fid, group=group)
            try:
                with gf.file.open('rb') as f:
                    all_pdf_bytes.append(f.read())
                if not file_name:
                    file_name = gf.name
            except (FileNotFoundError, OSError):
                messages.error(
                    request,
                    f"Le fichier « {gf.name} » n'est plus disponible. Veuillez le re-uploader."
                )
                return render(request, 'courses/group/course_create_wizard.html', {
                    'group': group, 'group_files': group_files
                })

        # 2) Nouveaux fichiers — lire les bytes en mémoire SANS créer en BDD
        # La création en BDD se fait dans la transaction atomique ci-dessous
        pending_new_files: list[tuple[str, bytes, object]] = []  # (fname, bytes, InMemoryUploadedFile)
        for i, uploaded in enumerate(new_files_all):
            if len(all_pdf_bytes) >= 3:
                break
            fname = new_names_all[i].strip() if i < len(new_names_all) and new_names_all[i].strip() else uploaded.name
            raw = uploaded.read()
            all_pdf_bytes.append(raw)
            pending_new_files.append((fname, raw, uploaded))
            if not file_name:
                file_name = fname

        if not all_pdf_bytes:
            return JsonResponse({'error': 'Veuillez sélectionner au moins un fichier.'}, status=400)

        if not title:
            title = file_name

        # Garantit l'unicité même si deux requêtes arrivent simultanément
        title = _unique_title(title, group)

        nb_sources = len(all_pdf_bytes)

        try:
            # Extraction multi-sources (chaque PDF séparément pour préserver la structure)
            pdf_text = extract_pdf_text(all_pdf_bytes)
            if not pdf_text.strip():
                return JsonResponse(
                    {'error': "Impossible d'extraire du texte (PDF scanné ou vide ?)."},
                    status=400
                )

            slides_data    = generate_slides(pdf_text, nb_slides, nb_sources=nb_sources)
            questions_data = generate_questions(pdf_text, nb_questions, nb_sources=nb_sources)

            with transaction.atomic():
                # Créer les GroupFile uniquement si la génération a réussi
                for fname, raw, uploaded in pending_new_files:
                    gf = GroupFile(group=group, name=fname, uploaded_by=person)
                    gf.file.save(uploaded.name, ContentFile(raw), save=True)

                course = Course.objects.create(
                    title=title, group=group, created_by=person,
                    nb_slides=nb_slides, nb_questions=nb_questions,
                    is_published=False,
                )
                Slide.objects.bulk_create([
                    Slide(course=course, order=s.get('order', i + 1), content=s.get('content', ''))
                    for i, s in enumerate(slides_data)
                ])
                Question.objects.bulk_create([
                    Question(
                        course=course, order=q.get('order', i + 1),
                        text=q.get('text', ''), choice_a=q.get('choice_a', ''),
                        choice_b=q.get('choice_b', ''), choice_c=q.get('choice_c', ''),
                        choice_d=q.get('choice_d', ''), correct_answer=q.get('correct_answer', 'a'),
                        explanation=q.get('explanation', ''),
                    )
                    for i, q in enumerate(questions_data)
                ])

            messages.success(
                request,
                f"Cours « {title} » généré avec {len(slides_data)} slides "
                f"et {len(questions_data)} questions. Relisez avant de publier."
            )
            from django.urls import reverse
            return JsonResponse({'redirect': reverse('courses:review_slides', kwargs={'pk': course.pk})})

        except openai.RateLimitError:
            return JsonResponse(
                {'error': "Quota OpenAI dépassé. Patientez quelques instants puis réessayez."},
                status=429,
            )
        except openai.AuthenticationError:
            return JsonResponse(
                {'error': "Clé API OpenAI invalide ou manquante. Contactez l'administrateur."},
                status=500,
            )
        except openai.APIError as e:
            return JsonResponse(
                {'error': f"Erreur OpenAI : {e}"},
                status=502,
            )
        except Exception as e:
            return JsonResponse({'error': f'Erreur lors de la génération : {e}'}, status=500)

    existing_names = list(
        Course.objects.filter(group=group).values_list('title', flat=True)
    )
    return render(request, 'courses/group/course_create_wizard.html', {
        'group': group,
        'group_files': group_files,
        'existing_names': existing_names,
    })
