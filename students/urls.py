from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student_candidate_list/', views.student_candidate_list, name='student_candidate_list'),
    path('results/', views.student_results, name='student_result_page'),
    path('results-locked/', views.results_locked, name='results_locked'),
]