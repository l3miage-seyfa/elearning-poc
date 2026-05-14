from django.contrib import admin
from .models import Participation


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ['person', 'course', 'score', 'completed_at']
    list_filter = ['course', 'completed_at']
    search_fields = ['person__user__last_name', 'person__user__email']
    raw_id_fields = ['person', 'course']
