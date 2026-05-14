from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.models import Person
from services.decorators import login_and_person_required, responsible_required, admin_required
from .models import Group, GroupMembership


@login_and_person_required
def my_groups(request):
    person = request.user.person
    groups = Group.objects.filter(members=person).select_related('responsible', 'parent')
    return render(request, 'groups/my_groups.html', {'groups': groups})


@responsible_required
def group_detail(request, pk):
    person = request.user.person
    group = get_object_or_404(Group, pk=pk)

    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    members = group.memberships.select_related('person__user').order_by('joined_at')
    return render(request, 'groups/group_detail.html', {'group': group, 'members': members})


# ─── CRUD Groupes (admin uniquement) ──────────────────────────────────────────

@admin_required
def group_list(request):
    groups = Group.objects.select_related('responsible__user', 'parent').order_by('name')
    return render(request, 'groups/group_list.html', {'groups': groups})


@admin_required
def group_create(request):
    all_persons = Person.objects.select_related('user').order_by('user__last_name')
    all_groups  = Group.objects.order_by('name')

    if request.method == 'POST':
        name          = request.POST.get('name', '').strip()
        description   = request.POST.get('description', '').strip()
        group_type    = request.POST.get('type', 'equipe')
        parent_id     = request.POST.get('parent') or None
        responsible_id = request.POST.get('responsible')
        member_ids    = request.POST.getlist('members')

        if not name or not responsible_id:
            messages.error(request, "Le nom et le responsable sont requis.")
            return render(request, 'groups/group_form.html', {
                'action': 'Créer', 'all_persons': all_persons,
                'all_groups': all_groups, 'values': request.POST,
            })

        group = Group.objects.create(
            name=name, description=description, type=group_type,
            parent_id=parent_id, responsible_id=responsible_id,
        )
        # Ajouter les membres sélectionnés (le responsable est ajouté par Group.save())
        for mid in member_ids:
            GroupMembership.objects.get_or_create(group=group, person_id=mid)

        messages.success(request, f"Groupe « {group.name} » créé.")
        return redirect('groups:group_list')

    return render(request, 'groups/group_form.html', {
        'action': 'Créer', 'all_persons': all_persons,
        'all_groups': all_groups, 'values': {},
    })


@admin_required
def group_edit(request, pk):
    group       = get_object_or_404(Group, pk=pk)
    all_persons = Person.objects.select_related('user').order_by('user__last_name')
    all_groups  = Group.objects.exclude(pk=pk).order_by('name')
    current_member_ids = list(group.members.values_list('pk', flat=True))

    if request.method == 'POST':
        group.name        = request.POST.get('name', '').strip()
        group.description = request.POST.get('description', '').strip()
        group.type        = request.POST.get('type', 'equipe')
        group.parent_id   = request.POST.get('parent') or None
        group.responsible_id = request.POST.get('responsible')
        group.save()

        # Resync membres
        new_member_ids = [int(i) for i in request.POST.getlist('members')]
        # Responsable toujours membre (déjà géré par save, mais on l'inclut dans le set)
        new_member_ids_set = set(new_member_ids)
        # Supprime membres retirés (sauf responsable)
        GroupMembership.objects.filter(group=group).exclude(
            person_id__in=new_member_ids_set
        ).exclude(person=group.responsible).delete()
        # Ajoute nouveaux membres
        for mid in new_member_ids_set:
            GroupMembership.objects.get_or_create(group=group, person_id=mid)

        messages.success(request, f"Groupe « {group.name} » mis à jour.")
        return redirect('groups:group_list')

    return render(request, 'groups/group_form.html', {
        'action': 'Modifier', 'group': group,
        'all_persons': all_persons, 'all_groups': all_groups,
        'current_member_ids': current_member_ids,
        'values': {
            'name': group.name, 'description': group.description,
            'type': group.type, 'parent': group.parent_id,
            'responsible': group.responsible_id,
        },
    })


@admin_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f"Groupe « {name} » supprimé.")
        return redirect('groups:group_list')
    return render(request, 'groups/group_confirm_delete.html', {'group': group})


