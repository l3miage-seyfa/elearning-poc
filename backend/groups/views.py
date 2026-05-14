from django.shortcuts import render, get_object_or_404
from services.decorators import login_and_person_required, responsible_required
from .models import Group


@login_and_person_required
def my_groups(request):
    """Liste des groupes dont l'utilisateur est membre."""
    person = request.user.person
    groups = Group.objects.filter(members=person).select_related('responsible', 'parent')
    return render(request, 'groups/my_groups.html', {'groups': groups})


@responsible_required
def group_detail(request, pk):
    """Détail d'un groupe — accessible au responsable et aux admins."""
    person = request.user.person
    group = get_object_or_404(Group, pk=pk)

    # Un non-admin ne peut voir que ses groupes
    if not person.is_admin and group.responsible != person:
        from django.http import Http404
        raise Http404

    members = group.memberships.select_related('person__user').order_by('joined_at')
    return render(request, 'groups/group_detail.html', {'group': group, 'members': members})

