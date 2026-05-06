from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('vote/', views.vote_page, name='vote_page'),
    path('submit-vote/', views.submit_vote, name='submit_vote'),
    path('candidates/<int:id>/', views.candidate_detail, name='candidate_detail'),
    path("live-votes/", views.live_votes, name="live_votes"),

    # ================= ADMIN URLS =================
    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('admin_election_list/', views.admin_election_list, name='admin_election_list'),
    path('admin_candidate_list/', views.admin_candidate_list, name='admin_candidate_list'),
    path("admin/elections/<int:election_id>/results/", views.admin_election_results, name="admin_election_results"
),
]