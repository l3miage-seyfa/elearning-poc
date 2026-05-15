from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import FileResponse, Http404
from services.decorators import login_and_person_required, responsible_required
from groups.models import Group


def _assert_file_access(person, group):
    """Lève Http404 si l'utilisateur n'a pas accès aux fichiers du groupe."""
    is_member = group.members.filter(pk=person.pk).exists()
    if not (person.is_admin or group.responsible == person or is_member):
        raise Http404


def _assert_responsible(person, group):
    """Lève Http404 si l'utilisateur n'est pas responsable/admin."""
    if not person.is_admin and group.responsible != person:
        raise Http404


@responsible_required
def group_file_upload(request, pk):
    """Upload un fichier dans le groupe."""
    from groups.models import GroupFile
    group  = get_object_or_404(Group, pk=pk)
    person = request.user.person
    _assert_responsible(person, group)

    if request.method == 'POST':
        uploaded = request.FILES.get('file')
        name     = request.POST.get('name', '').strip()
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
    group  = get_object_or_404(Group, pk=pk)
    person = request.user.person
    _assert_responsible(person, group)

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
    """Téléchargement sécurisé d'un fichier du groupe."""
    from groups.models import GroupFile
    group  = get_object_or_404(Group, pk=pk)
    person = request.user.person
    _assert_file_access(person, group)
    gf = get_object_or_404(GroupFile, pk=file_pk, group=group)
    try:
        return FileResponse(gf.file.open('rb'), as_attachment=True, filename=f"{gf.name}.pdf")
    except FileNotFoundError:
        raise Http404


@login_and_person_required
def group_file_view(request, pk, file_pk):
    """Affiche un fichier PDF en inline (iframe, pas de téléchargement forcé)."""
    from groups.models import GroupFile
    group  = get_object_or_404(Group, pk=pk)
    person = request.user.person
    _assert_file_access(person, group)
    gf = get_object_or_404(GroupFile, pk=file_pk, group=group)
    try:
        response = FileResponse(gf.file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{gf.name}.pdf"'
        return response
    except FileNotFoundError:
        raise Http404


@responsible_required
def group_file_delete(request, pk, file_pk):
    """Supprime un fichier du groupe."""
    from groups.models import GroupFile
    group  = get_object_or_404(Group, pk=pk)
    person = request.user.person
    _assert_responsible(person, group)

    gf = get_object_or_404(GroupFile, pk=file_pk, group=group)
    if request.method == 'POST':
        name = gf.name
        gf.file.delete(save=False)
        gf.delete()
        messages.success(request, f"Fichier « {name} » supprimé.")
    return redirect('courses:responsible_group', pk=pk)
