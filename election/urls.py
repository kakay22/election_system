from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('vote/', views.vote_page, name='vote_page'),
    path('submit-vote/', views.submit_vote, name='submit_vote'),
    path('candidates/<int:id>/', views.candidate_detail, name='candidate_detail'),
    path("live-votes/", views.live_votes, name="live_votes"),
]