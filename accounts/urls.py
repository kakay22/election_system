from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.student_register, name='student_register'),
    path('login/', views.student_login, name='student_login'),
    path('logout/', views.logout, name='logout'),
]