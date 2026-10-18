from django.contrib import admin
from .models import Faculty,Specialty,Subject,UserProfile,Resource,ToDo,ActivityLog,NewsPost,ContactMessage
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    search_fields=("name",)
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display=("name","faculty","cycle"); list_filter=("faculty","cycle"); search_fields=("name","faculty__name")
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display=("name","specialty","code"); list_filter=("specialty__faculty","specialty"); search_fields=("name","code")
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display=("user","role","semester","specialty","current_year"); list_filter=("role","semester","specialty","current_year"); search_fields=("user__username","user__email")
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display=("title","author","category","subject","submitted_by","is_verified","created_at"); list_filter=("category","is_verified","subject"); search_fields=("title","author","description")
@admin.register(ToDo)
class ToDoAdmin(admin.ModelAdmin):
    list_display=("title","subject","created_by","assigned_to","due_date","is_completed"); list_filter=("is_completed","due_date","subject")

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display=("action","user","created_at"); readonly_fields=("user","action","details","created_at")

@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display=("faculty","author","link_url","created_at"); list_filter=("faculty","author"); search_fields=("content","link_url","faculty__name","author__username")

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display=("category","username","contact_name","email","message","created_at")
    list_filter=("category","created_at")
    search_fields=("username","contact_name","email","message")
    readonly_fields=("user","username","contact_name","email","category","message","created_at")
