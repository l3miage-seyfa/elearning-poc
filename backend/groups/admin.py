from django.contrib import admin
from .models import Group, GroupMembership


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1
    raw_id_fields = ['person']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'responsible', 'parent', 'member_count']
    list_filter = ['type']
    search_fields = ['name']
    raw_id_fields = ['responsible', 'parent']
    inlines = [GroupMembershipInline]

    @admin.display(description="Membres")
    def member_count(self, obj):
        return obj.members.count()


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['person', 'group', 'joined_at']
    list_filter = ['group']
    raw_id_fields = ['person', 'group']
