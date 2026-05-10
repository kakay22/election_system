from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Candidate, Election, PartyList, Position, Student, Vote, VotingSession
from django.db.models import Count


def landing_page(request):
    election = Election.objects.first()
    now = timezone.now()

    countdown_type = "closed"
    target_date = None

    if election and election.is_active:

        if now < election.start_datetime:
            countdown_type = "starts_in"
            target_date = election.start_datetime

        elif election.start_datetime <= now <= election.end_datetime:
            countdown_type = "ends_in"
            target_date = election.end_datetime

        else:
            countdown_type = "closed"

    candidates = (
        Candidate.objects.filter(is_active=True)
        .select_related("position", "party")
        .annotate(votes_count=Count("vote"))
    )

    positions = (
        Candidate.objects.filter(is_active=True)
        .values_list("position__name", flat=True)
        .distinct()
    )

    context = {
        "election": election,
        "countdown_type": countdown_type,
        "target_date": target_date,
        "total_candidates": Candidate.objects.filter(is_active=True).count(),
        "total_votes": Vote.objects.count(),
        "total_parties": PartyList.objects.count(),
        "candidates": candidates,
        "parties": PartyList.objects.all(),
        "positions": positions,
    }

    return render(request, "landing_page.html", context)


def live_votes(request):
    candidates = (
        Candidate.objects.filter(is_active=True)
        .annotate(votes_count=Count("vote"))
        .values("id", "votes_count")
    )

    data = {candidate["id"]: candidate["votes_count"] for candidate in candidates}
    return JsonResponse(data)


def vote_page(request):
    student = get_logged_in_student(request)
    if not student:
        return redirect("student_login")

    election = Election.objects.filter(is_active=True).first()
    if not election:
        return render(request, "no_election.html")

    if not election.is_open():
        return render(request, "election_closed.html")

    already_voted = VotingSession.objects.filter(
        student=student,
        election=election,
        has_submitted=True,
    ).exists()

    if already_voted:
        return render(request, "students/already_voted.html")

    positions = Position.objects.filter(election=election).order_by("order")
    candidates = (
        Candidate.objects.filter(election=election, is_active=True)
        .select_related("position")
        .order_by("position__order", "full_name")
    )

    candidates_by_position = {position.id: [] for position in positions}
    for candidate in candidates:
        candidates_by_position[candidate.position_id].append(candidate)

    positions_with_candidates = [
        {
            "position": position,
            "candidates": candidates_by_position[position.id],
        }
        for position in positions
    ]

    context = {
        "election": election,
        "positions_with_candidates": positions_with_candidates,
    }

    return render(request, "students/vote_page.html", context)


@transaction.atomic
def submit_vote(request):
    if request.method != "POST":
        return redirect("vote_page")

    student = get_logged_in_student(request)
    if not student:
        return redirect("student_login")

    election = Election.objects.filter(is_active=True).first()
    if not election or not election.is_open():
        messages.error(request, "Election is not active.")
        return redirect("vote_page")

    session, _ = VotingSession.objects.get_or_create(
        student=student,
        election=election,
    )

    if session.has_submitted:
        messages.error(request, "You already voted.")
        return redirect("vote_page")

    selected_votes = get_selected_votes(request.POST, election)
    if selected_votes is None:
        messages.error(request, "Invalid vote selection.")
        return redirect("vote_page")

    for position, candidate in selected_votes:
        Vote.objects.create(
            student=student,
            election=election,
            position=position,
            candidate=candidate,
        )

    session.has_submitted = True
    session.submitted_at = timezone.now()
    session.save(update_fields=["has_submitted", "submitted_at"])

    if hasattr(student, "has_voted"):
        student.has_voted = True
        student.save(update_fields=["has_voted"])

    messages.success(request, "Vote submitted successfully!")
    return redirect("vote_page")


def candidate_detail(request, id):
    candidate = get_object_or_404(Candidate, id=id)
    return render(
        request,
        "students/student_candidate_detail.html",
        {"candidate": candidate},
    )


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")

        messages.error(request, "Invalid credentials or not authorized.")

    return render(request, "admins/admin_login.html")

def admin_dashboard(request):
    students = Student.objects.count()
    candidates = Candidate.objects.count()
    votes = Vote.objects.count()

    positions = Position.objects.all().order_by('order')

    chart_data = {}

    for position in positions:
        votes_data = (
            Vote.objects.filter(position=position)
            .values('candidate__full_name')
            .annotate(total_votes=Count('id'))
        )

        chart_data[position.id] = {
            "name": position.name,
            "labels": [v['candidate__full_name'] for v in votes_data],
            "votes": [v['total_votes'] for v in votes_data],
        }

    context = {
        "students": students,
        "candidates": candidates,
        "votes": votes,
        "positions": positions,
        "chart_data": chart_data
    }

    return render(request, "admins/admin_dashboard.html", context)

@login_required(login_url="admin_login")
def admin_election_list(request):
    if not request.user.is_superuser:
        return redirect("admin_login")

    if request.method == "POST":
        election = get_object_or_404(Election, id=request.POST.get("election_id"))
        election.is_active = not election.is_active
        election.save(update_fields=["is_active"])

        return redirect("admin_election_list")

    return render(
        request,
        "admins/admin_elections.html",
        {"elections": Election.objects.all()},
    )


@login_required(login_url="admin_login")
def admin_candidate_list(request):
    if not request.user.is_superuser:
        return redirect("admin_login")

    return render(
        request,
        "admins/admin_candidates.html",
        {"candidates": Candidate.objects.all()},
    )


def get_logged_in_student(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return None

    return Student.objects.filter(student_id=student_id).first()


def get_selected_votes(post_data, election):
    selected_votes = []

    for key, candidate_id in post_data.items():
        if not key.startswith("position_"):
            continue

        position_id = key.removeprefix("position_")
        position = Position.objects.filter(id=position_id, election=election).first()
        candidate = Candidate.objects.filter(
            id=candidate_id,
            election=election,
            position=position,
            is_active=True,
        ).first()

        if not position or not candidate:
            return None

        selected_votes.append((position, candidate))

    return selected_votes

def admin_election_results(request, election_id):
    election = Election.objects.get(id=election_id)

    candidates = Candidate.objects.filter(election=election).annotate(
        vote_count=Count('vote')
    )

    return render(request, "admins/admin_election_result.html", {
        "election": election,
        "candidates": candidates
    })