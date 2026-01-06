from django.urls import path
from .views import event_trigger

urlpatterns = [
    path("event-trigger/", event_trigger),
]
