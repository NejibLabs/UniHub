from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
urlpatterns = [
 path("admin/",admin.site.urls), path("",views.home,name="home"),
 path("admin-dashboard/",views.admin_dashboard,name="admin_dashboard"),
 path("register/",views.register,name="register"), path("login/",views.login_view,name="login"),
 path("logout/",views.logout_view,name="logout"), path("student-form/",views.student_form,name="student_form"),
 path("student-hub/",views.dashboard,name="dashboard"), path("news/",views.news_feed,name="news_feed"), path("subjects/",views.subject_list,name="subject_list"),
 path("my-specialty/",views.specialty_subjects,name="specialty_subjects"),
 path("subject/<int:subject_id>/",views.subject_vault,name="subject_vault"),
 path("subject/<int:subject_id>/resources/add/",views.add_resource,name="add_resource"),
 path("resources/<int:resource_id>/verify/",views.verify_resource,name="verify_resource"),
 path("subject/<int:subject_id>/tasks/add/",views.add_task,name="add_task"),
 path("tasks/<int:task_id>/toggle/",views.toggle_task,name="toggle_task"),
 path("profile/",views.profile,name="profile"), path("search/",views.search,name="search"), path("about/",views.about,name="about"),
 path("contact/",views.contact,name="contact"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
