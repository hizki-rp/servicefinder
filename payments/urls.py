from django.urls import path
from . import views

urlpatterns = [
    path('recent/', views.recent_payments, name='recent_payments'),
    path('today/', views.todays_payments, name='todays_payments'),
]