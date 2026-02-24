from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/analyze/', views.analyze, name='analyze'),
    path('api/history/', views.history, name='history'),
    path('api/clear/', views.clear, name='clear'),
    path('api/agent/', views.agent, name='agent'),
]
