from .models import Election
from django.utils import timezone


def get_election_status():
    election = Election.objects.first()

    if not election:
        return {
            "status": "none",
            "election": None
        }

    now = timezone.now()

    if election.start_datetime and now < election.start_datetime:
        return {
            "status": "upcoming",
            "election": election
        }

    if election.end_datetime and now > election.end_datetime:
        return {
            "status": "closed",
            "election": election
        }

    if election.is_active:
        return {
            "status": "active",
            "election": election
        }

    return {
        "status": "closed",
        "election": election
    }