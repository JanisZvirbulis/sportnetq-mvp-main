from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone
from users.models import User
from .models import TeamMember, Event, AttendanceRecord, Team, PhysicalAssessmentScore, PhysicalAssessmentRecord, OrganizationPhysicalAssessmentScore, OrganizationPhysicalAssessmentRecord

def createTeamMemberEventAttendanceRecord(sender, instance, created, **kwargs):
    if created:
        event = instance
        team = Team.objects.get(pk=event.teamID.id)
        team_members = team.teammember_set.filter(role=1, is_active=True)
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
        team_members = team.teammember_set.filter(role=1, is_active=True)
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

def OrganizationCreateTeamMemberPhisycalAssesmentScore(sender, instance, created, **kwargs):
    if created:
        pa_record = instance
        team = Team.objects.get(pk=pa_record.team.id)
        team_members = team.teammember_set.filter(role=1, is_active=True)
        assessment_type = pa_record.org_physical_assessment.assessment_type
        if assessment_type == 'score':
            for member in team_members:
                createMemberPaScore = OrganizationPhysicalAssessmentScore.objects.create(
                    team = team,
                    organization = team.organization,
                    org_physical_assessment = pa_record.org_physical_assessment,
                    org_physical_assessment_record = pa_record,
                    team_member = member,
                    score = 0.0
                )
                createMemberPaScore.save()
        if assessment_type == 'distance':
            for member in team_members:
                createMemberPaScore = OrganizationPhysicalAssessmentScore.objects.create(
                    team = team,
                    organization = team.organization,
                    org_physical_assessment = pa_record.org_physical_assessment,
                    org_physical_assessment_record = pa_record,
                    team_member = member,
                    distance = 0.0
                )
                createMemberPaScore.save()
        if assessment_type == 'time':
            for member in team_members:
                createMemberPaScore = OrganizationPhysicalAssessmentScore.objects.create(
                    team = team,
                    organization = team.organization,
                    org_physical_assessment = pa_record.org_physical_assessment,
                    org_physical_assessment_record = pa_record,
                    team_member = member,
                    time = timedelta(seconds=0)
                )
                createMemberPaScore.save()


def delete_attendance_records(sender, instance, **kwargs):
    if not instance.is_active:
        # Fetch all attendance records for this team member where the event date is in the future
        future_records = AttendanceRecord.objects.filter(team_member=instance, event__start_time__gte=timezone.now())
        # Delete attendance records with EMPTYVALUE
        future_records.filter(attendance=AttendanceRecord.EMPTYVALUE).delete()

def create_attendance_records(sender, instance, created, **kwargs):
    if created or instance.is_active:
        if instance.role == '1':  # Check if the role is Athlete
            # Fetch upcoming events for the team
            upcoming_events = Event.objects.filter(teamID=instance.teamID, start_time__gte=timezone.now())
            # Create attendance records with EMPTYVALUE for each upcoming event
            for event in upcoming_events:
                AttendanceRecord.objects.get_or_create(team_member=instance, event=event, team=instance.teamID, attendance=AttendanceRecord.EMPTYVALUE)


post_save.connect(createTeamMemberPhisycalAssesmentScore, sender=PhysicalAssessmentRecord)
post_save.connect(createTeamMemberEventAttendanceRecord, sender=Event)
post_save.connect(OrganizationCreateTeamMemberPhisycalAssesmentScore, sender=OrganizationPhysicalAssessmentRecord)
post_save.connect(create_attendance_records, sender=TeamMember)
pre_save.connect(delete_attendance_records, sender=TeamMember)
