from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from services.decorators import login_and_person_required, responsible_required
from groups.models import Group
from courses.models import Course


@responsible_required
def responsible_group_detail(request, pk):
    """Page groupe du responsable : membres, fichiers, participations, cours."""
    from groups.models import GroupFile
    from participations.models import Participation
    person = request.user.person
    group  = get_object_or_404(Group, pk=pk)

    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    if request.method == 'POST' and 'update_description' in request.POST:
        group.description = request.POST.get('description', '').strip()
        group.save()
        messages.success(request, "Description mise à jour.")
        return redirect('courses:responsible_group', pk=pk)

    members = group.memberships.select_related('person__user').order_by('person__user__last_name')
    courses = Course.objects.filter(group=group).order_by('-created_at')

    participations_by_course = {}
    for course in courses:
        participations_by_course[course.pk] = Participation.objects.filter(
            course=course
        ).select_related('person__user').order_by('-completed_at')

    group_files = group.files.select_related('uploaded_by__user').order_by('-uploaded_at')

    return render(request, 'courses/group/responsible_group.html', {
        'group':                  group,
        'members':                members,
        'courses':                courses,
        'participations_by_course': participations_by_course,
        'group_files':            group_files,
    })


@responsible_required
def group_add_member(request, pk):
    """Ajoute un membre au groupe via son email (POST uniquement)."""
    from accounts.models import Person as PersonModel
    from groups.models import GroupMembership
    group  = get_object_or_404(Group, pk=pk)
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
    group  = get_object_or_404(Group, pk=pk)
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
    from accounts.models import Person as PersonModel
    q       = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        persons = PersonModel.objects.filter(
            user__email__icontains=q
        ).select_related('user').order_by('user__email')[:10]
        results = [
            {'email': p.user.email, 'name': p.user.get_full_name()}
            for p in persons
        ]
    return JsonResponse({'results': results})
