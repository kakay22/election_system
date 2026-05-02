from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Election, Position, Candidate, Student, Vote, VotingSession, PartyList
from django.db import transaction

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count

from .models import Election, Candidate, Vote, Position

def landing_page(request):
    election = Election.objects.first()
    now = timezone.now()

    countdown_type = None
    target_date = None

    # ================= ELECTION STATUS =================
    if election:
        if now < election.start_datetime:
            countdown_type = "starts_in"
            target_date = election.start_datetime

        elif election.start_datetime <= now <= election.end_datetime:
            countdown_type = "ends_in"
            target_date = election.end_datetime

        else:
            countdown_type = "closed"

    # ================= STATS =================
    total_candidates = Candidate.objects.filter(is_active=True).count()
    total_votes = Vote.objects.count()
    total_parties = PartyList.objects.count()

    # ================= CANDIDATES WITH VOTE COUNT =================
    candidates = (
        Candidate.objects
        .filter(is_active=True)
        .select_related("position", "party")  # 🔥 optimization
        .annotate(votes_count=Count("vote"))  # 🔥 key feature
        .order_by("-votes_count")[:6]         # 🔥 top candidates
    )

    # ================= POSITIONS FOR FILTER =================
    positions = (
        Candidate.objects
        .filter(is_active=True)
        .values_list("position__name", flat=True)
        .distinct()
    )

    # ================= PARTIES =================
    parties = PartyList.objects.all()

    context = {
        "election": election,
        "countdown_type": countdown_type,
        "target_date": target_date,
        "total_candidates": total_candidates,
        "total_votes": total_votes,
        "total_parties": total_parties,
        "candidates": candidates,
        "parties": parties,
        "positions": positions,  # 🔥 needed for dropdown
    }

    return render(request, "landing_page.html", context)

from django.http import JsonResponse
from django.db.models import Count

def live_votes(request):
    candidates = (
        Candidate.objects.filter(is_active=True)
        .annotate(votes_count=Count("vote"))
        .values("id", "votes_count")
    )

    data = {c["id"]: c["votes_count"] for c in candidates}
    return JsonResponse(data)

def vote_page(request):
    student_id = request.session.get('student_id')

    student = Student.objects.get(student_id=student_id)

    election = Election.objects.filter(is_active=True).first()

    if not election:
        return render(request, "no_election.html")

    if not election.is_open():
        return render(request, "election_closed.html")

    # prevent already voted students
    if VotingSession.objects.filter(student_id=student, election=election, has_submitted=True).exists():
        return render(request, "students/already_voted.html")

    positions = Position.objects.filter(election=election).order_by('order')
    candidates = Candidate.objects.filter(election=election, is_active=True)

    context = {
        'election': election,
        'positions': positions,
        'candidates': candidates,
    }

    return render(request, 'students/vote_page.html', context)


@transaction.atomic
def submit_vote(request):
    if request.method != "POST":
        return redirect('vote_page')

    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = Student.objects.get(student_id=student_id)
    election = Election.objects.filter(is_active=True).first()

    if not election or not election.is_open():
        messages.error(request, "Election is not active.")
        return redirect('vote_page')

    # prevent double voting
    session, created = VotingSession.objects.get_or_create(
        student=student,
        election=election
    )

    if session.has_submitted:
        messages.error(request, "You already voted.")
        return redirect('vote_page')

    # 🔥 get all selected votes from form
    for key, value in request.POST.items():
        if key.startswith("position_"):
            position_id = key.split("_")[1]
            candidate_id = value

            position = Position.objects.get(id=position_id)
            candidate = Candidate.objects.get(id=candidate_id)

            # save vote
            Vote.objects.create(
                student=student,
                election=election,
                position=position,
                candidate=candidate
            )

    # mark as submitted
    session.has_submitted = True
    session.submitted_at = timezone.now()
    session.save()

    student.has_voted = True
    student.save()

    messages.success(request, "Vote submitted successfully!")
    return redirect('vote_page')


def candidate_detail(request, id):
    candidate = Candidate.objects.get(id=id)

    return render(request, "students/student_candidate_detail.html", {
        "candidate": candidate
    })