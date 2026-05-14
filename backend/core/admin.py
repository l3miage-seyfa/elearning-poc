from django.contrib import admin
from .models import Person, Group, GroupMembership, Course, Slide, Question, Participation


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1


class SlideInline(admin.TabularInline):
    model = Slide
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_admin')
    list_filter = ('is_admin',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'parent', 'responsible')
    list_filter = ('type',)
    inlines = [GroupMembershipInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'is_published', 'created_at')
    list_filter = ('is_published', 'group')
    inlines = [SlideInline, QuestionInline]


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('person', 'course', 'score', 'completed_at')
    list_filter = ('course',)
