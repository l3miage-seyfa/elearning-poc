# courses/views/__init__.py
# Point d'entrée unique — réexporte toutes les vues pour que urls.py
# continue d'utiliser `from . import views` sans modification.

from .admin   import admin_dashboard
from .member  import member_courses
from .group   import (
    responsible_group_detail,
    group_add_member,
    group_remove_member,
    member_autocomplete,
)
from .files   import (
    group_file_upload,
    group_file_rename,
    group_file_download,
    group_file_view,
    group_file_delete,
)
from .wizard  import course_create_wizard
from .review  import (
    review_slides,
    review_questions,
    preview_questions,
    course_publish,
    course_delete,
)

__all__ = [
    'admin_dashboard', 'course_create', 'upload_pdf_view',
    'member_courses',
    'responsible_group_detail', 'group_add_member', 'group_remove_member', 'member_autocomplete',
    'group_file_upload', 'group_file_rename', 'group_file_download', 'group_file_view', 'group_file_delete',
    'course_create_wizard',
    'review_slides', 'review_questions', 'preview_questions', 'course_publish', 'course_delete',
]
