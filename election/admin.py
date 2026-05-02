from django.contrib import admin
from .models import Student, Election, Position, Candidate, Vote, VotingSession, VoteLog, PartyList


# ================================
# 👨‍🎓 STUDENT ADMIN
# ================================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'course', 'year_level', 'is_active')
    search_fields = ('student_id', 'first_name', 'last_name')
    list_filter = ('course', 'year_level', 'is_active')


# ================================
# 🏛 ELECTION ADMIN
# ================================
@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)


# ================================
# 🗳 POSITION ADMIN
# ================================
@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'election', 'max_vote', 'order')
    list_filter = ('election',)
    ordering = ('election', 'order')


# ================================
# 🧑‍💼 CANDIDATE ADMIN
# ================================
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'party', 'is_active')
    list_filter = ('position', 'party', 'is_active')
    search_fields = ('full_name',)


# ================================
# 🗳 VOTE ADMIN (READ ONLY)
# ================================
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'candidate', 'position', 'election', 'voted_at')
    list_filter = ('election', 'position')
    search_fields = ('student__student_id', 'candidate__full_name')

    # 🔒 prevent editing votes (important for integrity)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ================================
# 🧾 VOTING SESSION ADMIN
# ================================
@admin.register(VotingSession)
class VotingSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'election', 'has_submitted', 'submitted_at')
    list_filter = ('election', 'has_submitted')
    search_fields = ('student__student_id',)


# ================================
# 🔐 VOTE LOG ADMIN (OPTIONAL)
# ================================
@admin.register(VoteLog)
class VoteLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'action', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('student__student_id',)
    readonly_fields = ('timestamp',)

@admin.register(PartyList)
class PartyListAdmin(admin.ModelAdmin):
    list_display = ('name', 'election', 'get_candidates_count', 'is_active')
    list_filter = ('election', 'is_active')
    search_fields = ('name', 'slogan', 'description')

    ordering = ('election', 'name')

    def get_candidates_count(self, obj):
        return obj.candidates.count()

    get_candidates_count.short_description = "Candidates"