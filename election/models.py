from django.db import models
from django.contrib.auth.models import AbstractUser


# ================================
# 👨‍🎓 STUDENT 
# ================================
class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    year_level = models.IntegerField()

    password = models.CharField(max_length=255)  # hashed later
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"


# ================================
# 🏛 ELECTION
# ================================
class Election(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def is_open(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_datetime <= now <= self.end_datetime


# ================================
# 🗳 POSITION
# ================================
class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    name = models.CharField(max_length=100)
    max_vote = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.election.title})"


# ================================
# 🏛 PARTY LIST 
class PartyList(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='parties')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    logo = models.ImageField(upload_to='party_logos/', blank=True, null=True)

    slogan = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.election.title})"

# ================================
# 🧑‍💼 CANDIDATE
# ================================
class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')

    full_name = models.CharField(max_length=255)
    party = models.ForeignKey(PartyList, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates')

    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    campaign_description = models.TextField()

    qualifications = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    eligibility = models.TextField(blank=True)
    platform = models.TextField(blank=True)

    course = models.CharField(max_length=100, blank=True, null=True)
    year_level = models.CharField(max_length=20, blank=True, null=True)
    section = models.CharField(max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.full_name} - {self.position.name}"


# ================================
# 🗳 VOTE (Audit Trail)
# ================================
class Vote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='votes')
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'position', 'election'],
                name='unique_vote_per_position'
            )
        ]

    def __str__(self):
        return f"{self.student} -> {self.candidate}"


# ================================
# 🧾 VOTING SESSION (Prevent Double Voting)
# ================================
class VotingSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    has_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'election')

    def __str__(self):
        return f"{self.student} - {self.election} - Submitted: {self.has_submitted}"


# ================================
# 🔐 OPTIONAL: LOGS (ADVANCED)
# ================================
class VoteLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('VOTE', 'Vote'),
        ('SUBMIT', 'Submit Ballot'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.action} - {self.timestamp}"