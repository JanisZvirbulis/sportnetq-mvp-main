from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta
from users.models import User
from .models import TeamMember, Event, AttendanceRecord, Team, PhysicalAssessmentScore, PhysicalAssessmentRecord

def createTeamMemberEventAttendanceRecord(sender, instance, created, **kwargs):
    if created:
        event = instance
        team = Team.objects.get(pk=event.teamID.id)
        team_members = team.teammember_set.filter(role=1)
        for member in team_members:
            createMemberAttendace = AttendanceRecord.objects.create(
                team_member = member,
                event = event,
                attendance = '1',
                team = team,
            )
            createMemberAttendace.save()

def createTeamMemberPhisycalAssesmentScore(sender, instance, created, **kwargs):
    if created:
        pa_record = instance
        team = Team.objects.get(pk=pa_record.team.id)
        team_members = team.teammember_set.filter(role=1)
        assessment_type = pa_record.physical_assessment.assessment_type
        if assessment_type == 'score':
            for member in team_members:
                createMemberPaScore = PhysicalAssessmentScore.objects.create(
                    team = team,
                    physical_assessment = pa_record.physical_assessment,
                    physical_assessment_record = pa_record,
                    team_member = member,
                    score = 0.0
                )
                createMemberPaScore.save()
        if assessment_type == 'distance':
            for member in team_members:
                createMemberPaScore = PhysicalAssessmentScore.objects.create(
                    team = team,
                    physical_assessment = pa_record.physical_assessment,
                    physical_assessment_record = pa_record,
                    team_member = member,
                    distance = 0.0
                )
                createMemberPaScore.save()
        if assessment_type == 'time':
            for member in team_members:
                createMemberPaScore = PhysicalAssessmentScore.objects.create(
                    team = team,
                    physical_assessment = pa_record.physical_assessment,
                    physical_assessment_record = pa_record,
                    team_member = member,
                    time = timedelta(seconds=0)
                )
                createMemberPaScore.save()

# def createTeamMemberPhisycalAssesmentScore(sender, instance, created, **kwargs):
#     if created:
#         pa_record = instance
#         team = Team.objects.get(pk=pa_record.team.id)

#         # Fetch members who are athletes
#         team_members = team.teammember_set.filter(user__profile__user_type=Profile.ATHLETE)

#         assessment_type = pa_record.physical_assessment.assessment_type
#         if assessment_type == 'score':
#             for member in team_members:
#                 createMemberPaScore = PhysicalAssessmentScore.objects.create(
#                     team = team,
#                     physical_assessment = pa_record.physical_assessment,
#                     physical_assessment_record = pa_record,
#                     team_member = member,
#                     score = 0.0
#                 )
#                 createMemberPaScore.save()
#         if assessment_type == 'distance':
#             for member in team_members:
#                 createMemberPaScore = PhysicalAssessmentScore.objects.create(
#                     team = team,
#                     physical_assessment = pa_record.physical_assessment,
#                     physical_assessment_record = pa_record,
#                     team_member = member,
#                     distance = 0.0
#                 )
#                 createMemberPaScore.save()
#         if assessment_type == 'time':
#             for member in team_members:
#                 createMemberPaScore = PhysicalAssessmentScore.objects.create(
#                     team = team,
#                     physical_assessment = pa_record.physical_assessment,
#                     physical_assessment_record = pa_record,
#                     team_member = member,
#                     time = timedelta(seconds=0)
#                 )
#                 createMemberPaScore.save()


post_save.connect(createTeamMemberPhisycalAssesmentScore, sender=PhysicalAssessmentRecord)
post_save.connect(createTeamMemberEventAttendanceRecord, sender=Event)

