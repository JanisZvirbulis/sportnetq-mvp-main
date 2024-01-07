from django.contrib import admin
from .models import Team, Event, TeamMember, AttendanceRecord, PhysicalAssessment, PhysicalAssessmentScore, PhysicalAssessmentRecord, Invitation, TeamSeason, TeamTactic, TacticImage, AthleteInvitation, TeamNotification, NotificationLink, AthleteMarkForEvent, OrganizationPhysicalAssessmentRecord, OrganizationPhysicalAssessmentScore
# Register your models here.

admin.site.register(Team)
admin.site.register(Event)
admin.site.register(TeamMember)
admin.site.register(AttendanceRecord)
admin.site.register(PhysicalAssessment)
admin.site.register(PhysicalAssessmentScore)
admin.site.register(PhysicalAssessmentRecord)
admin.site.register(Invitation)
admin.site.register(TeamSeason)
admin.site.register(TeamTactic)
admin.site.register(TacticImage)
admin.site.register(AthleteInvitation)
admin.site.register(TeamNotification)
admin.site.register(NotificationLink)
admin.site.register(AthleteMarkForEvent)
admin.site.register(OrganizationPhysicalAssessmentRecord)
admin.site.register(OrganizationPhysicalAssessmentScore)
