from .utils import get_election_status


def election_status(request):
    return get_election_status()