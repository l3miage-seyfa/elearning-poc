from django.contrib import admin
from .models import Course, Slide, Question


class SlideInline(admin.TabularInline):
    model = Slide
    extra = 0
    fields = ['order', 'content']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['order', 'text', 'choice_a', 'choice_b', 'choice_c', 'choice_d', 'correct_answer']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'created_by', 'is_published', 'nb_slides', 'nb_questions', 'created_at']
    list_filter = ['is_published', 'group']
    search_fields = ['title']
    raw_id_fields = ['group', 'created_by']
    inlines = [SlideInline, QuestionInline]
    actions = ['publish', 'unpublish']

    @admin.action(description="Publier les cours sélectionnés")
    def publish(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Dépublier les cours sélectionnés")
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ['course', 'order']
    list_filter = ['course']
    ordering = ['course', 'order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['course', 'order', 'text', 'correct_answer']
    list_filter = ['course']
    ordering = ['course', 'order']
