from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login),
    path("logout", views.logout),
    path("", views.overview),
    path("alerts", views.alerts),
    path("students", views.students),
    path("students/<int:pk>", views.student_detail),
    path("reveal/<str:kind>/<int:pk>", views.reveal),
    path("providers", views.providers),
    path("providers/<str:code>", views.provider_detail),
    path("groups", views.groups),
    path("groups/<str:code>", views.group_detail),
    path("instructors", views.instructors),
    path("instructors/<int:pk>", views.instructor_detail),
    path("attendance", views.attendance),
    path("attendance/<int:pk>", views.lecture_detail),
    path("inbox", views.inbox),
    path("inbox/<int:pk>", views.inbox),
    path("inbox/<int:pk>/send", views.inbox_send),
    path("tickets", views.tickets),
    path("tickets/<str:code>", views.ticket_detail),
    path("tickets/<str:code>/status", views.ticket_status),
    path("projects", views.projects),
    path("forms", views.forms),
    path("imports", views.imports),
    path("audit", views.audit_log),
    path("settings", views.settings_page),
]
