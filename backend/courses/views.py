import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from services.decorators import login_and_person_required, admin_required, responsible_required
from services.ai_service import extract_pdf_text, generate_slides, generate_questions
from services.storage_service import upload_pdf
from groups.models import Group
from .models import Course, Slide, Question


@admin_required
def admin_dashboard(request):
    """Vue principale de l'admin : compteurs + liste des cours."""
    from accounts.models import Person
    from participations.models import Participation

    courses = Course.objects.select_related('group', 'created_by__user').order_by('-created_at')
    groups  = Group.objects.all()

    stats = {
        'nb_persons':      Person.objects.count(),
        'nb_groups':       Group.objects.count(),
        'nb_courses':      courses.count(),
        'nb_published':    courses.filter(is_published=True).count(),
        'nb_participations': Participation.objects.count(),
    }
    return render(request, 'courses/admin_dashboard.html', {
        'courses': courses,
        'groups':  groups,
        'stats':   stats,
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

    # Ajoute les participations existantes (dernière tentative par cours)
    from participations.models import Participation
    participations = Participation.objects.filter(person=person, score__isnull=False).order_by('-completed_at')
    # Garde uniquement la dernière tentative par cours
    seen = set()
    participated_ids = set()
    participated_pks = {}
    for p in participations:
        if p.course_id not in seen:
            seen.add(p.course_id)
            participated_ids.add(p.course_id)
            participated_pks[p.course_id] = p.pk

    return render(request, 'courses/member_courses.html', {
        'courses': courses,
        'participated_ids': participated_ids,
        'participated_pks': participated_pks,
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
    preselect_group_id = request.GET.get('group_id') or request.POST.get('group_id')
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

                course.is_published = False
                course.save()

            messages.success(
                request,
                f"Cours « {course.title} » généré avec {len(slides_data)} slides "
                f"et {len(questions_data)} questions. Relisez et publiez."
            )
            return redirect('courses:review_slides', pk=course.pk)

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération : {e}")

    return render(request, 'courses/upload_pdf.html', {
        'groups': groups,
        'existing_course': existing_course,
        'preselect_group_id': preselect_group_id,
    })


# ─── Phase 4 : interface responsable de groupe ──────────────────────────────────


@responsible_required
def responsible_group_detail(request, pk):
    """Page groupe du responsable : membres, fichiers, participations, cours du groupe."""
    from groups.models import GroupMembership, GroupFile
    from participations.models import Participation
    person = request.user.person
    group = get_object_or_404(Group, pk=pk)

    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    if request.method == 'POST' and 'update_description' in request.POST:
        new_desc = request.POST.get('description', '').strip()
        group.description = new_desc
        group.save()
        messages.success(request, "Description mise à jour.")
        return redirect('courses:responsible_group', pk=pk)

    members = group.memberships.select_related('person__user').order_by('person__user__last_name')
    courses = Course.objects.filter(group=group).order_by('-created_at')

    # Participations pour chaque cours du groupe
    participations_by_course = {}
    for course in courses:
        participations_by_course[course.pk] = Participation.objects.filter(
            course=course
        ).select_related('person__user').order_by('-completed_at')

    group_files = group.files.select_related('uploaded_by__user').order_by('-uploaded_at')

    return render(request, 'courses/responsible_group.html', {
        'group': group,
        'members': members,
        'courses': courses,
        'participations_by_course': participations_by_course,
        'group_files': group_files,
    })


# ─── Gestion des fichiers du groupe ────────────────────────────────────────────

@responsible_required
def group_file_upload(request, pk):
    """Upload un fichier dans le groupe."""
    from groups.models import GroupFile
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person
    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    if request.method == 'POST':
        uploaded = request.FILES.get('file')
        name = request.POST.get('name', '').strip()
        if not uploaded:
            messages.error(request, "Veuillez sélectionner un fichier.")
        elif not name:
            messages.error(request, "Veuillez donner un nom au fichier.")
        else:
            GroupFile.objects.create(group=group, name=name, file=uploaded, uploaded_by=person)
            messages.success(request, f"Fichier « {name} » ajouté.")
    return redirect('courses:responsible_group', pk=pk)


@responsible_required
def group_file_rename(request, pk, file_pk):
    """Renomme un fichier du groupe."""
    from groups.models import GroupFile
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person
    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    gf = get_object_or_404(GroupFile, pk=file_pk, group=group)
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            gf.name = new_name
            gf.save()
            messages.success(request, f"Fichier renommé en « {new_name} ».")
        else:
            messages.error(request, "Le nom ne peut pas être vide.")
    return redirect('courses:responsible_group', pk=pk)


@login_and_person_required
def group_file_download(request, pk, file_pk):
    """Téléchargement sécurisé d'un fichier du groupe (membres + responsable + admin uniquement)."""
    from groups.models import GroupFile
    from django.http import FileResponse, Http404
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person
    # Vérifier que l'utilisateur est membre, responsable ou admin
    is_member = group.members.filter(pk=person.pk).exists()
    if not (person.is_admin or group.responsible == person or is_member):
        raise Http404
    gf = get_object_or_404(GroupFile, pk=file_pk, group=group)
    try:
        return FileResponse(gf.file.open('rb'), as_attachment=True, filename=f"{gf.name}.pdf")
    except FileNotFoundError:
        raise Http404


@responsible_required
def group_file_delete(request, pk, file_pk):
    """Supprime un fichier du groupe."""
    from groups.models import GroupFile
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person
    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    gf = get_object_or_404(GroupFile, pk=file_pk, group=group)
    if request.method == 'POST':
        name = gf.name
        gf.file.delete(save=False)
        gf.delete()
        messages.success(request, f"Fichier « {name} » supprimé.")
    return redirect('courses:responsible_group', pk=pk)


# ─── Wizard création de cours depuis un fichier ────────────────────────────────

@responsible_required
def course_create_wizard(request, pk):
    """
    Wizard création de cours pour un groupe.
    Étape unique : choisir un fichier existant OU uploader un nouveau,
    saisir titre/nb_slides/nb_questions, puis générer avec GPT-4o.
    """
    from groups.models import GroupFile
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person
    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    group_files = group.files.order_by('-uploaded_at')

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        nb_slides   = int(request.POST.get('nb_slides', 5))
        nb_questions = int(request.POST.get('nb_questions', 5))
        file_source = request.POST.get('file_source', 'existing')  # 'existing' ou 'new'

        pdf_bytes = None
        file_name = ''

        if file_source == 'new':
            uploaded_files = request.FILES.getlist('new_file[]')
            file_names     = request.POST.getlist('new_file_name[]')
            # Compat ancien format (champ unique)
            if not uploaded_files:
                single = request.FILES.get('new_file')
                if single:
                    uploaded_files = [single]
                    file_names     = [request.POST.get('new_file_name', '').strip()]
            if not uploaded_files:
                messages.error(request, "Veuillez sélectionner un fichier.")
                return render(request, 'courses/course_create_wizard.html', {
                    'group': group, 'group_files': group_files
                })
            # Sauvegarde tous les fichiers dans la bibliothèque du groupe
            saved_gfs = []
            for i, uploaded in enumerate(uploaded_files):
                fname = file_names[i].strip() if i < len(file_names) and file_names[i].strip() else uploaded.name
                gf = GroupFile.objects.create(
                    group=group, name=fname,
                    file=uploaded, uploaded_by=person
                )
                saved_gfs.append(gf)
            # Utilise le premier fichier pour générer le cours
            primary_gf = saved_gfs[0]
            primary_gf.file.seek(0)
            pdf_bytes = primary_gf.file.read()
            file_name = primary_gf.name
        else:
            file_id = request.POST.get('file_id')
            if not file_id:
                messages.error(request, "Veuillez choisir un fichier.")
                return render(request, 'courses/course_create_wizard.html', {
                    'group': group, 'group_files': group_files
                })
            gf = get_object_or_404(GroupFile, pk=file_id, group=group)
            with gf.file.open('rb') as f:
                pdf_bytes = f.read()
            file_name = gf.name

        if not title:
            title = file_name

        try:
            pdf_text = extract_pdf_text(pdf_bytes)
            if not pdf_text.strip():
                messages.error(request, "Impossible d'extraire du texte de ce fichier (PDF scanné ?).")
                return render(request, 'courses/course_create_wizard.html', {
                    'group': group, 'group_files': group_files
                })

            slides_data    = generate_slides(pdf_text, nb_slides)
            questions_data = generate_questions(pdf_text, nb_questions)

            with transaction.atomic():
                course = Course.objects.create(
                    title=title, group=group, created_by=person,
                    nb_slides=nb_slides, nb_questions=nb_questions,
                    is_published=False,
                )
                Slide.objects.bulk_create([
                    Slide(course=course, order=s.get('order', i+1), content=s.get('content', ''))
                    for i, s in enumerate(slides_data)
                ])
                Question.objects.bulk_create([
                    Question(
                        course=course, order=q.get('order', i+1),
                        text=q.get('text', ''), choice_a=q.get('choice_a', ''),
                        choice_b=q.get('choice_b', ''), choice_c=q.get('choice_c', ''),
                        choice_d=q.get('choice_d', ''), correct_answer=q.get('correct_answer', 'a'),
                        explanation=q.get('explanation', ''),
                    )
                    for i, q in enumerate(questions_data)
                ])

            messages.success(request, f"Cours « {title} » généré avec {len(slides_data)} slides et {len(questions_data)} questions. Relisez avant de publier.")
            return redirect('courses:review_slides', pk=course.pk)

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération : {e}")

    return render(request, 'courses/course_create_wizard.html', {
        'group': group, 'group_files': group_files
    })


@responsible_required
def group_add_member(request, pk):
    """Ajoute un membre au groupe via son email (POST uniquement)."""
    from accounts.models import Person as PersonModel
    from groups.models import GroupMembership
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person

    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            target = PersonModel.objects.get(user__email__iexact=email)
            _, created = GroupMembership.objects.get_or_create(person=target, group=group)
            if created:
                messages.success(request, f"{target.user.get_full_name()} ({email}) ajouté au groupe.")
            else:
                messages.info(request, f"{target.user.get_full_name()} est déjà membre de ce groupe.")
        except PersonModel.DoesNotExist:
            messages.error(request, f"Aucun utilisateur trouvé avec l'email « {email} ».")

    return redirect('courses:responsible_group', pk=pk)


@responsible_required
def group_remove_member(request, pk, person_pk):
    """Retire un membre du groupe (POST uniquement)."""
    from accounts.models import Person as PersonModel
    from groups.models import GroupMembership
    group = get_object_or_404(Group, pk=pk)
    person = request.user.person

    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    if request.method == 'POST':
        target = get_object_or_404(PersonModel, pk=person_pk)
        if target == group.responsible:
            messages.error(request, "Impossible de retirer le responsable du groupe.")
        else:
            GroupMembership.objects.filter(person=target, group=group).delete()
            messages.success(request, f"{target.user.get_full_name()} retiré du groupe.")

    return redirect('courses:responsible_group', pk=pk)


@login_and_person_required
def member_autocomplete(request):
    """Retourne les membres en JSON pour l'autocomplete (email contient le terme)."""
    import json
    from accounts.models import Person as PersonModel
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        persons = PersonModel.objects.filter(
            user__email__icontains=q
        ).select_related('user').order_by('user__email')[:10]
        results = [
            {'email': p.user.email, 'name': p.user.get_full_name()}
            for p in persons
        ]
    from django.http import JsonResponse
    return JsonResponse({'results': results})


# ─── Phase 5 : review & édition avant publication ───────────────────────────────

def _can_edit_course(person, course):
    return person.is_admin or course.created_by == person or \
           course.group.responsible == person


@login_and_person_required
def review_slides(request, pk):
    """Review + édition de toutes les slides avant publication."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        from django.http import Http404
        raise Http404

    slides = list(course.slides.order_by('order'))

    if request.method == 'POST':
        with transaction.atomic():
            for slide in slides:
                new_content = request.POST.get(f'slide_{slide.pk}', '').strip()
                if new_content != slide.content:
                    slide.content = new_content
                    slide.save()
        messages.success(request, "Slides sauvegardées.")
        return redirect('courses:review_questions', pk=course.pk)

    return render(request, 'courses/review_slides.html', {
        'course': course, 'slides': slides
    })


@login_and_person_required
def review_questions(request, pk):
    """Review + édition de toutes les questions avant publication."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        from django.http import Http404
        raise Http404

    questions = list(course.questions.order_by('order'))

    if request.method == 'POST':
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
        messages.success(request, "Questions sauvegardées.")
        return redirect('courses:review_questions', pk=course.pk)

    return render(request, 'courses/review_questions.html', {
        'course': course, 'questions': questions
    })


@login_and_person_required
def course_publish(request, pk):
    """Publie (ou dépublie) un cours."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        from django.http import Http404
        raise Http404
    if request.method == 'POST':
        course.is_published = not course.is_published
        course.save()
        status = "publié" if course.is_published else "dépublié"
        messages.success(request, f"Cours « {course.title} » {status}.")
    return redirect('courses:responsible_group', pk=course.group.pk)


@login_and_person_required
def course_delete(request, pk):
    """Supprime un cours (responsable ou admin uniquement)."""
    course = get_object_or_404(Course, pk=pk)
    person = request.user.person
    if not _can_edit_course(person, course):
        from django.http import Http404
        raise Http404
    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f"Cours « {title} » supprimé.")
        if person.is_admin:
            return redirect('courses:admin_dashboard')
        return redirect('groups:responsible_group', pk=course.group_id)
    return render(request, 'courses/course_confirm_delete.html', {'course': course})

