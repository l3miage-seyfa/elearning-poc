from django.contrib import admin
from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'email', 'is_admin']
    list_filter = ['is_admin']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    raw_id_fields = ['user']

    @admin.display(description="Nom complet")
    def full_name(self, obj):
        return obj.user.get_full_name()

    @admin.display(description="Email")
    def email(self, obj):
        return obj.user.email
