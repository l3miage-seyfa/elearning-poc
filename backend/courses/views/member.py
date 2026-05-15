from django.shortcuts import render
from services.decorators import login_and_person_required
from groups.models import Group
from courses.models import Course


@login_and_person_required
def member_courses(request):
    """Vue membre : cours publiés accessibles via les groupes (et leurs ancêtres)."""
    person = request.user.person

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

    from participations.models import Participation
    participations = Participation.objects.filter(
        person=person, score__isnull=False
    ).order_by('-completed_at')

    seen           = set()
    participated_ids = set()
    participated_pks = {}
    for p in participations:
        if p.course_id not in seen:
            seen.add(p.course_id)
            participated_ids.add(p.course_id)
            participated_pks[p.course_id] = p.pk

    return render(request, 'courses/member/member_courses.html', {
        'courses':          courses,
        'participated_ids': participated_ids,
        'participated_pks': participated_pks,
    })
