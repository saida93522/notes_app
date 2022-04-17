from django.urls import path
from .admin_views import populate_db

urlpatterns = [
    path('populate_db', populate_db, name='populate_db'),
]