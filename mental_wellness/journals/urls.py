from django.urls import path
from . import views

app_name = "journals"

urlpatterns = [
    path("", views.journal_page, name="journal_page"),
    path("submit/", views.submit_entry, name="submit"),
    path("edit/<int:entry_id>/", views.edit_entry, name="edit_entry"),
    path("delete/<int:entry_id>/", views.delete_entry, name="delete_entry"),
    path("toggle_pin/<int:entry_id>/", views.toggle_pin, name="toggle_pin"),
]
