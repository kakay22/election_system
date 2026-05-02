from django.shortcuts import render, redirect
from election.models import Student, Election, VotingSession, Candidate, Position, Vote
from django.contrib import messages
from election.utils import get_election_status


def student_dashboard(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('student_login')

    election = Election.objects.filter(is_active=True).first()

    status_data = get_election_status()

    has_voted = False
    if election:
        has_voted = VotingSession.objects.filter(
            student=student,
            election=election,
            has_submitted=True
        ).exists()

    context = {
        "student": student,
        "election": election,
        "election_status": status_data["status"],
        "has_voted": has_voted,
    }

    return render(request, "students/student_dashboard.html", context)

def student_candidate_list(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    election = Election.objects.filter(is_active=True).first()

    candidates = Candidate.objects.filter(election=election, is_active=True)

    return render(request, "students/student_candidate_list.html", {
        "candidates": candidates,
        "election": election,
    })

from django.shortcuts import render
from django.db.models import Count
from election.models import Election, Position, Candidate, Vote
from election.utils import get_election_status


def student_results(request):
    status_data = get_election_status()
    status = status_data["status"]
    election = status_data["election"]

    # 🔒 BLOCK results if election not finished
    if not election or status != "closed":
        return render(request, "results_locked.html")

    positions = Position.objects.filter(election=election)

    for position in positions:
        candidates = list(Candidate.objects.filter(position=position))

        # ✅ Get vote counts in ONE query
        vote_counts = (
            Vote.objects.filter(position=position)
            .values('candidate')
            .annotate(total=Count('id'))
        )

        # Convert to dictionary for fast lookup
        vote_dict = {v['candidate']: v['total'] for v in vote_counts}

        total_votes = sum(vote_dict.values())

        for candidate in candidates:
            count = vote_dict.get(candidate.id, 0)
            candidate.vote_count = count

            if total_votes > 0:
                candidate.percentage = (count / total_votes) * 100
            else:
                candidate.percentage = 0

        # ✅ SORT IN PYTHON (IMPORTANT FIX)
        candidates.sort(key=lambda x: x.vote_count, reverse=True)

        # ✅ SAFE custom attribute
        position.candidates_list = candidates

    return render(request, "students/student_result_page.html", {
        "election": election,
        "positions": positions
    })

def results_locked(request):
    return render(request, "students/results_locked.html")