import csv
import calendar
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Prefetch, Avg
from django.conf import settings
from django.utils.translation import gettext as _
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from PIL import Image
from io import BytesIO
from calendar import monthrange
from dateutil.rrule import rrule, WEEKLY
from datetime import datetime, timedelta, date, time
from .models import Team, Event, TeamMember, AttendanceRecord, PhysicalAssessment, PhysicalAssessmentScore, PhysicalAssessmentRecord, TeamSeason, TeamTactic, TacticImage, TeamNotification, NotificationLink, ATHLETE, COUNTRY_CHOICES, AthleteMarkForEvent, OrganizationPhysicalAssessmentRecord, OrganizationPhysicalAssessmentScore
from .forms import TeamForm, EventForm, CreateEventForm, AttendanceRecordForm, AddAttendanceRecordForm, PhysicalAssessmentForm, PhysicalAssessmentRecordForm, PhysicalAssessmentScoreForm, InvitationForm, AthleteInvitationForm, TeamMemberForm, TeamSeasonForm, SingleTeamSeasonForm, TacticForm, TacticImageForm, AddTeamMemberScoreToPhysicalAssessmentRecord, EmailNotificationForm, TeamNotificationLinkForm, AthleteMarkForEventForm, OrgPhysicalAssessmentRecordForm, OrgPhysicalAssessmentScoreForm, PhysicalAssessmentChoiceForm, OrgPhysicalAssessmentChoiceForm, TeamAnalyticsDateForm
from users.models import Profile
from organizations.models import OrganizationPhysicalAssessment
from .utils import Calendar, generate_attendance_data, generate_team_members_data, generate_event_data, generate_teammember_attendace_data, generate_event_subcategories, transform_event_subcategories, custom_forbidden, get_event_type_label, send_notification_byemail, generate_happened_event_data, generate_happened_athlete_event_data

OWNER_ROLE = '4'

def user_is_team_member(view_func):
    def _wrapped_view(request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])

        try:
            member = TeamMember.objects.select_related('profileID').get(profileID=request.user.profile, teamID=team, is_active=True)
        except TeamMember.DoesNotExist:
            return custom_forbidden(request, _("You are not a member of this team."))
        
        team_members = TeamMember.objects.select_related('profileID').filter(teamID=team, is_active=True)

        request.team = team
        request.member = member
        request.team_members = team_members

        return view_func(request, *args, **kwargs)

    return _wrapped_view

def user_is_member_and_have_access(view_func):
    def _wrapped_view(request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])

        # Fetch team_member and profile in a single query using select_related
        try:
            team_member = TeamMember.objects.select_related('profileID').get(profileID=request.user.profile, teamID=team, is_active=True)
        except TeamMember.DoesNotExist:
            return custom_forbidden(request, _("You are not a member of this team."))
        
        if team_member.role not in ['2', '4']:
            return custom_forbidden(request, _("You do not have the required permissions to access this page."))
        
        request.team = team
        request.current_user_member = team_member
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def user_is_owner(view_func):
    def _wrapped_view(request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        try:
            team_member = TeamMember.objects.select_related('profileID').get(profileID=request.user.profile, teamID=team, is_active=True)
        except TeamMember.DoesNotExist:
            return custom_forbidden(request, _("You are not a member of this team."))
        
        if team_member.role != OWNER_ROLE:
            return custom_forbidden(request, _("You must be the team owner to access this page."))
        
        request.team = team
        request.current_user_member = team_member
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def user_is_team_owner(view_func):
    def _wrapped_view(request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        try:
            team_member = TeamMember.objects.select_related('profileID', 'teamID').get(profileID=request.user.profile, teamID=team, is_active=True)
        except TeamMember.DoesNotExist:
            return custom_forbidden(request, _("You are not a member of this team."))
        
        if team_member.role != OWNER_ROLE:
            return custom_forbidden(request, _("You must be the team owner to access this page."))
        
        request.team = team
        request.current_user_member = team_member
        return view_func(request, *args, **kwargs)

    return _wrapped_view


@login_required(login_url="login")
@user_is_owner
def deleteTeam(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    if request.method == 'POST':
        team.delete()
        return redirect('teams')
    context = {'teamObj': team, 'role':role}
    return render(request, 'teams/deletetemplates/delete_team_template.html', context)
    


@login_required(login_url="login")
def teams(request):
    requserid = request.user.profile.id
    teams = TeamMember.objects.select_related('teamID').filter(profileID=requserid, is_active=True)
    context = {'teams': teams}

    return render(request, 'teams/teams.html', context)


@login_required(login_url="login")
@user_is_team_member
def team(request, pk):
    team = request.team
    current_user = request.member
    team_members = request.team_members.order_by('profileID__name')
    role = current_user.role

    events = team.events.filter(start_time__gt=timezone.now()).order_by('start_time')[:4]
    
    context = {'teamObj': team, 'role': role, 'events': events, 'team_members': team_members, 'COUNTRY_CHOICES': COUNTRY_CHOICES,}
    return render(request, 'teams/single-team.html', context)

@login_required(login_url="login")
@user_is_team_member
def teamMembers(request, pk):
    team = request.team
    current_user = request.member
    role = current_user.role
    team_members = request.team_members.order_by('role', 'profileID__name')
    sub_plan = team.organization.orgsubscriptionplan

    context = {'teamObj': team, 'members': team_members, 'role': role, 'sub_plan': sub_plan}
    return render(request, 'teams/team-members.html', context)

@login_required(login_url="login")
@user_is_team_owner
def editTeamMembers(request, pk):
    team = request.team
    current_user_member = request.current_user_member

    if current_user_member is None:
        return redirect('teams')

    role = current_user_member.role
    memberList = TeamMember.objects.filter(teamID=team, is_active=True).exclude(role='4').select_related('profileID').order_by('role', 'profileID__name')
    memberListFormSet = modelformset_factory(TeamMember, form=TeamMemberForm, extra=0)
    formset = memberListFormSet(queryset=memberList)

    if request.method == 'POST':
        formset = memberListFormSet(request.POST, queryset=memberList)
        if formset.is_valid():
            formset.save()
            return redirect('team-members', pk=team.id)
        else:
            messages.error(request, _('An error has occurred editing members'))

    return render(request, 'teams/team-members_form.html', {
        'teamObj': team,
        'members': memberList,
        'formset': formset,
        'role': role,
    })

@login_required(login_url="login")
@user_is_team_owner
def removeFromTeam(request, pk, memberid):

    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    # Fetch member using select_related to optimize queries
    member = get_object_or_404(TeamMember.objects.select_related('profileID', 'teamID'), id=memberid, teamID=pk, is_active=True)
    
    if member.profileID == team.owner:
        messages.error(request, _("You can't remove team owner from team"))
        return redirect('team-members', pk=team.id)
    
    if request.method == 'POST':
        member.delete()
        return redirect('team-members', pk=team.id)
    
    context = {'teamObj': team, 'object': member, 'role': role}
    return render(request, 'teams/deletetemplates/remove-member.html', context)

@login_required(login_url="login")
@user_is_owner
def invite_to_team(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    form = InvitationForm()
    context = {'teamObj': team, 'role': role, 'form': form}
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            try:
                invited_user_profile = Profile.objects.get(user__email=email)
            except Profile.DoesNotExist:
                messages.error(request, _("The email provided does not belong to any registered user. "))
                return render(request, 'teams/invite_to_team.html', context)
            if team.teammember_set.filter(profileID=invited_user_profile, is_active=True).exists():
                messages.warning(request, _("The user is already a member of this team. "))
                return render(request, 'teams/invite_to_team.html', context)
            inviteForm = form.save(commit=False)
            inviteForm.email = email
            inviteForm.team = team
            inviteForm.save()

             # Send email
            #  VAJAG IZTULKOT f STRINGUS
            subject = f'{_("You have been invited to join %(team)s team") % {"team":inviteForm.team}}'
            accept_invite_url = reverse("accept-invitation", args=[inviteForm.token])
            message = f'{_("Please click the link to accept the invitation from %(team)s team") % {"team": inviteForm.team}}: {request.build_absolute_uri(accept_invite_url)}'
            # message = f'Please click the link to accept the invitation from {inviteForm.team}: http://127.0.0.1:8000/accept-invite/{inviteForm.token}/'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list, fail_silently=False,)

            messages.success(request, _('Invitation have been sent '))
            return redirect('team-members', pk=team.id)
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))
   
    return render(request, 'teams/invite_to_team.html', context)

@login_required(login_url="login")
@user_is_owner
def inviteAthleteToSignUp(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    form = AthleteInvitationForm()
    context = {'teamObj': team, 'role': role, 'form': form}
    if request.method == 'POST':
        form = AthleteInvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            try:
                invited_user_profile = Profile.objects.get(user__email=email)
                messages.error(request, _("User with this email is already registered to SportNetQ."))
                return redirect('invite-athlete-signup', pk=team.id)
            except Profile.DoesNotExist:
                # save invite
                inviteForm = form.save(commit=False)
                inviteForm.email = email
                inviteForm.team = team
                inviteForm.invited_by = current_user_member.profileID
                inviteForm.save()
                # Send invite to register
                subject = f'{_("You have been invited to Sign Up at SportNetQ and join %(team)s team") % {"team":inviteForm.team}}'
                accept_invite_url = reverse("register", args=[inviteForm.token])
                message = f'{_("Please click the link to Sign Up at SportNetQ as athlete and join team %(team)s team") % {"team": inviteForm.team}}: {request.build_absolute_uri(accept_invite_url)}'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [email]

                send_mail(subject, message, from_email, recipient_list, fail_silently=False,)

                messages.success(request, _("Invitation to athlete registration has been sent to %(email)s") % {'email': email} )
                return redirect('team-members', pk=team.id) 
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))
                
    return render(request, 'teams/invite-athlete-signup.html', context)
            

# CALENDAR
@login_required(login_url="login")
@user_is_team_member
def teamScheduleAll(request, pk):

    current_user = request.member
    role = current_user.role
    
    d = get_date(request.GET.get('month', None))
    team = request.team
    cal = Calendar(d.year, d.month, pk, team)          
    html_cal = cal.formatmonth(withyear=True)
    calendar =  html_cal
    prevm = prev_month(d)
    nextm = next_month(d)
    context = {'teamObj': team, 'role': role, 'calendar': calendar, 'prev_month': prevm, 'next_month': nextm}
    return render(request, 'teams/schedule.html',context)

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

# TeamEvent CRUD
@login_required(login_url="login")
@user_is_member_and_have_access
def createTeamEvent(request, pk):
    
    page = 'Create' 
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    notifications = TeamNotification.objects.filter(team=team)
    form = CreateEventForm(notifications=notifications)

    if request.method == 'POST':
        form = CreateEventForm(request.POST, notifications=notifications)
        if form.is_valid():
            recurrence = form.cleaned_data['recurrence']
            recurrence_end_date = form.cleaned_data['recurrence_end_date']
            start_datetime = form.cleaned_data['start_time']

            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime, timezone.get_default_timezone())

            start_date = start_datetime.date()
            max_end_date = start_date + relativedelta(months=3)  # 3 months from start_datetime

            if recurrence == 'weekly':
                if recurrence_end_date is None:
                    messages.error(request, _("Please set a recurrence end date for weekly events."))
                    context = {'teamObj': team, 'form': form, 'role': role, 'page': page}
                    return render(request, 'teams/team-event_form.html', context)
                elif start_date > recurrence_end_date:
                    messages.error(request, _("Recurrence end date can't be before start date"))
                    context = {'teamObj': team, 'form': form, 'role': role, 'page': page}
                    return render(request, 'teams/team-event_form.html', context)
                elif recurrence_end_date > max_end_date:
                    messages.error(request, _("You can't schedle weekly events that are over 3 months from start date"))
                    context = {'teamObj': team, 'form': form, 'role': role, 'page': page}
                    return render(request, 'teams/team-event_form.html', context)

            if recurrence == 'none':
                event = form.save(commit=False)
                event.teamID = team
                event.save()
            elif recurrence == 'weekly':
                start_time = start_datetime.time()  # Extract time component

                for event_date in rrule(WEEKLY, dtstart=start_date, until=recurrence_end_date):
                    combined_datetime = datetime.combine(event_date, start_time)

                    if timezone.is_naive(combined_datetime):
                        combined_datetime = timezone.make_aware(combined_datetime, timezone.get_default_timezone())

                    Event.objects.create(
                        teamID=team,
                        start_time=combined_datetime,
                        title=form.cleaned_data['title'],
                        type=form.cleaned_data['type'],
                        comment=form.cleaned_data['comment'],
                        send_email_notification=form.cleaned_data['send_email_notification'],
                        email_notification=form.cleaned_data['email_notification']
                    )

            return redirect('team-schedule', pk=team.id)
        else:
            messages.error(request, _('Invalid form submission. Please check your input.'))


    context = {'teamObj': team, 'form': form, 'role': role, 'page': page}
    return render(request, 'teams/team-event_form.html', context)

@login_required(login_url="login")
@user_is_team_member
def viewTeamEvent(request, pk, eid):
    team = request.team
    current_user_member = request.member
    role = current_user_member.role
    event = get_object_or_404(Event, id=eid, teamID=pk)
    attendance = AttendanceRecord.objects.filter(event=event, team_member__is_active=True).select_related('team_member__profileID').order_by('team_member__profileID__name')
    # Initialize variables
    existing_mark = None
    form = None
    submitted_mark = None
    # Check if the current time is after the event start time
    if timezone.now().date() >= event.start_time.date():
        # Check if a mark has already been submitted
        if role != ATHLETE:
            marks = AthleteMarkForEvent.objects.filter(event=event)
            average_mark = marks.aggregate(Avg('mark'))['mark__avg']
        else:
            average_mark = None
            existing_mark = AthleteMarkForEvent.objects.filter(member=current_user_member, event=event).first()

            if not existing_mark:
                form = AthleteMarkForEventForm(request.POST or None)
                if request.method == 'POST' and form.is_valid():
                    athlete_mark = form.save(commit=False)
                    athlete_mark.member = current_user_member
                    athlete_mark.event = event
                    athlete_mark.save()
                    return redirect('team-event', pk=team.id, eid=event.id)
            else:
                submitted_mark = existing_mark.mark
    else:
        average_mark = None

    context = {
        'teamObj': team, 
        'role': role, 
        'event': event, 
        'attendance': attendance, 
        'form': form, 
        'submitted_mark': submitted_mark,
        'average_mark': average_mark
    }
    return render(request, 'teams/team-event.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def editTeamEvent(request, pk, eid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    page = 'Edit' 

    event = get_object_or_404(Event, id=eid, teamID=pk)
    if not event:
        return redirect('team-schedule', pk=team.id)
    notifications = TeamNotification.objects.filter(team=team)
    form = EventForm(instance=event, notifications=notifications)
    if request.method == 'POST':
        form = EventForm(request.POST,instance=event,notifications=notifications)
        if form.is_valid():
            teamEvent = form.save(commit=False)
            teamEvent.save()
            return redirect('team-event', pk=team.id, eid=teamEvent.id)
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))
    context = {'teamObj': team, 'form': form , 'role': role, 'page': page, 'event': event }         
    return render(request, 'teams/team-event_form.html',context)

@login_required(login_url="login")
@user_is_member_and_have_access
def deleteTeamEvent(request, pk, eid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    # Fetch event by id and teamID
    event = get_object_or_404(Event, id=eid, teamID=team.id)
    
    if request.method == 'POST':
        event.delete()
        return redirect('team-schedule', pk=team.id)
    
    # Pass the team object in the context
    context = {'teamObj': team, 'object': event, 'role': role}
    return render(request, 'teams/deletetemplates/delete_template.html', context)

# TeamEvent  attendance CRUD
@login_required(login_url="login")
@user_is_member_and_have_access
def TeamEventAttendance(request, pk, eventid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    event = get_object_or_404(Event, id=eventid, teamID=pk)
    
    # Retrieve attendance_records and also fetch related team_member and profileID data
    attendance_records = AttendanceRecord.objects.select_related('team_member__profileID').filter(event_id=eventid, team_member__teamID=team, team_member__is_active=True).order_by('team_member__profileID__name')
    AttendanceRecordFormSet = modelformset_factory(AttendanceRecord, form=AttendanceRecordForm, extra=0)
    formset = AttendanceRecordFormSet(queryset=attendance_records)
    if request.method == 'POST':
        formset = AttendanceRecordFormSet(request.POST, queryset=attendance_records)
        if formset.is_valid():
            instances = formset.save(commit=False)  # Use commit=False to get instances without saving to the database

            if event.send_email_notification: # check if need to send email for this event
                # Collect email addresses of members whose attendance is updated to ATTENDED and email_notification_sent is False
                attended_members_emails = [
                    instance.team_member.profileID.email 
                    for instance in instances 
                    if instance.attendance == '2' and not instance.email_notification_sent
                ]

                # Send email notification to attended members
                if attended_members_emails:
                    notification = event.email_notification

                    if notification:
                        # Fetch all links associated with the notification
                        notification_links = notification.links.all()

                        # Construct a string with all link titles and URLs
                        links_str = "\n".join([f"{link.title}: {link.url}" for link in notification_links])

                        # Combine the message with the links
                        combined_message = f"{notification.message}\n{links_str}"
                        message = combined_message
                    else:
                        formatted_start_time = event.start_time.strftime('%Y-%m-%d %H:%M')
                        # In case there's no custom notification message, format a default message
                        message = f'''
                        Your attendance has been updated to "ATTENDED" for the "{event.teamID}" event,
                        which was scheduled at "{formatted_start_time}".
                        '''
                    message = message
                    event_type_str = get_event_type_label(event.type)
                    formatted_start_time = event.start_time.strftime('%Y-%m-%d %H:%M')
                    subject = f' SportNetQ: You got new task from team - "{event.teamID}" - Event "{event_type_str}" Scheduled for "{formatted_start_time}" '


                    send_notification_byemail(subject, message, attended_members_emails)
                    # Update instances to mark email_notification_sent as True
                    for instance in instances:
                        if instance.attendance == '2' and not instance.email_notification_sent:
                            instance.email_notification_sent = True
                            instance.save()

            formset.save()  # Save the instances with email_notification_sent updated
            return redirect('team-event', pk=team.id, eid=event.id)
        else:
            messages.error(request, _('An error has occurred editing attendance'))
    else:
    # Prepopulate formset for GET requests
        for form in formset:
            if form.instance.attendance == AttendanceRecord.EMPTYVALUE:
                form.initial['attendance'] = AttendanceRecord.ATTENDED
                
    return render(request, 'teams/attendance_records.html', {
        'teamObj': team,
        'attendance_records': attendance_records,
        'formset': formset,
        'role': role,
        'event': event,
    })

@login_required(login_url="login")
@user_is_member_and_have_access
def addTeamMemberToEvent(request, pk, eventid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    event = get_object_or_404(Event, id=eventid, teamID=pk)
    # prefetch_related is used to efficiently fetch many-to-many and reverse foreign key relationships
    team_members = team.teammember_set.select_related('profileID').filter(role=1, is_active=True).order_by('profileID__name')


    
    form = AddAttendanceRecordForm(team_members=team_members)
    context = {'teamObj': team, 'role': role, 'form': form, 'event': event}

    if request.method == 'POST':
        userId = request.POST.get('team_member')
        if not userId or userId == None:
            messages.error(request, _("Please select a team member"))
            return render(request, 'teams/add-teammember-to-event.html', context)

        selectedTeamMember = TeamMember.objects.filter(profileID=userId, teamID=team.id, is_active=True).first()

        if not selectedTeamMember:
            messages.error(request, _("You can't add a user who is not a team member"))
        elif AttendanceRecord.objects.filter(event=event, team_member=selectedTeamMember, team_member__is_active=True).exists():
            messages.error(request, _("Team member already has an attendance record for this event"))
        else:
            createMemberAttendance = AttendanceRecord.objects.create(
                team_member=selectedTeamMember,
                event=event,
                attendance='1',
                team=team,
            )
            createMemberAttendance.save()
            return redirect('attendance', pk=team.id, eventid=event.id)

    return render(request, 'teams/add-teammember-to-event.html', context)
# @login_required(login_url="login")
# @user_is_member_and_have_access
# def addTeamMemberToEvent(request, pk, eventid):
#     team = request.team
#     current_user_member = request.current_user_member

#     if current_user_member is None:
#         return redirect('teams')
    
#     role = current_user_member.role
#     team_members = team.teammember_set.filter(role=1)
#     event = get_object_or_404(Event, id=eventid, teamID=pk)
#     form = AddAttendanceRecordForm(team_members=team_members)
#     context = {'teamObj': team, 'role': role, 'form': form, 'event': event}
#     if request.method == 'POST':
#         userId = request.POST.get('team_member')
#         if not userId or userId == None:
#             messages.error(request, "Please select a team member")
#             return render(request, 'teams/add-teammember-to-event.html', context)

#         selectedTeamMember = TeamMember.objects.filter(profileID=userId, teamID=team.id).first()

#         if not selectedTeamMember:
#             messages.error(request, "You can't add a user who is not a team member")
#         elif AttendanceRecord.objects.filter(event=event, team_member=selectedTeamMember).exists():
#             messages.error(request, "Team member already has an attendance record for this event")
#         else:
#             createMemberAttendance = AttendanceRecord.objects.create(
#                 team_member=selectedTeamMember,
#                 event=event,
#                 attendance='1',
#                 team=team,
#             )
#             createMemberAttendance.save()
#             return redirect('attendance', pk=team.id, eventid=event.id)


#     return render(request, 'teams/add-teammember-to-event.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def removeTeamMemberFromEvent(request, pk, eventid, attendanceid):
    # Using team from request context to avoid redundant query
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    
    # Fetch attendance_record using select_related to optimize queries
    attendance_record = get_object_or_404(AttendanceRecord.objects.select_related('team_member__profileID', 'event'), id=attendanceid, team=team.id, event=eventid)

    if request.method == 'POST':
        attendance_record.delete()
        return redirect('team-event', pk=pk, eid=eventid)
    
    # Pass the team object in the context
    context = {'teamObj': team, 'role': role, 'record': attendance_record}
    return render(request, 'teams/deletetemplates/delete_attendance.html', context)

# PhysicalAssessments all

@login_required(login_url="login")
@user_is_team_member
def allTeamPhysicalAssessment(request, pk):
    team = request.team
    current_user = request.member
    role = current_user.role

    physical_assessment_records = PhysicalAssessment.objects.filter(team=pk)
    org_physical_assessment_records = OrganizationPhysicalAssessment.objects.filter(organization=team.organization)
    context = {'teamObj': team,  'records': physical_assessment_records, 'org_records': org_physical_assessment_records, 'role': role}
    return render(request, 'teams/physical_assessments.html', context)

# Team PhysicalAssessments
@login_required(login_url="login")
@user_is_team_member
def singlePhysicalAssessment(request, pk, papk):
    team = request.team
    role = request.member.role

    physical_assessment = get_object_or_404(
        PhysicalAssessment.objects.select_related('team'),
        id=papk,
        team=team.id
    )

    physical_assessment_records = PhysicalAssessmentRecord.objects.filter(
        physical_assessment=physical_assessment,
        team=team
    ).only('physical_assessment_date').order_by('physical_assessment_date')

    physical_assessment_scores = PhysicalAssessmentScore.objects.filter(
        physical_assessment=physical_assessment,
        team=team,
        team_member__is_active=True
    ).prefetch_related(
        Prefetch('team_member', queryset=TeamMember.objects.select_related('profileID'))
    ).select_related('physical_assessment_record')

    scores_by_member_and_date = defaultdict(lambda: defaultdict(lambda: None))
    dates = PhysicalAssessmentScore.objects.filter(
        physical_assessment=physical_assessment,
        team=team,
        team_member__is_active=True
    ).values_list('physical_assessment_record__physical_assessment_date', flat=True).distinct()

    for score in physical_assessment_scores:
        scores_by_member_and_date[score.team_member][score.physical_assessment_record.physical_assessment_date] = score

    sorted_dates = sorted(list(dates))
    team_members = scores_by_member_and_date.keys()

    form = PhysicalAssessmentChoiceForm(request.POST or None, parecords=physical_assessment_records)
    
    if request.method == 'POST' and form.is_valid():
        selected_date = form.cleaned_data['pa_dates']
        if selected_date:
            return redirect('edit-physical-assessment-measurement', pk=team.id, papk=selected_date.physical_assessment.id, recordid=selected_date.id)
    
    context = {
        'teamObj': team,
        'record': physical_assessment,
        'role': role,
        'parecords': physical_assessment_records,
        'pa_score': physical_assessment_scores,
        'team_members': team_members,
        'dates': sorted_dates,
        'form': form,
        'scores_by_member_and_date': scores_by_member_and_date
    }
    return render(request, 'teams/physical_assessments_single.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def createPhysicalAssessment(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')

    role = current_user_member.role
    form = PhysicalAssessmentForm()
    
    if request.method == 'POST':
        form = PhysicalAssessmentForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.team = team
            record.save()
            return redirect('physical-assessments', pk=pk)
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))
    context = {'teamObj': team, 'role':role, 'form': form}
    return render(request, 'teams/create_physical_assessment.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def deletePhysicalAssessment(request, pk, papk):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    record = get_object_or_404(PhysicalAssessment, id=papk, team=pk)
    if request.method == 'POST':
        record.delete()
        return redirect('physical-assessments', pk=team.id)
    context = {'teamObj': team, 'role':role, 'record': record}
    return render(request, 'teams/deletetemplates/delete_physical_assessment.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def newPhysicalAssessmentMeasurement(request, pk, papk):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    physical_assessment = get_object_or_404(PhysicalAssessment, id=papk, team=pk)

    form = PhysicalAssessmentRecordForm()
    if request.method == 'POST':
        form = PhysicalAssessmentRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.physical_assessment = physical_assessment
            record.team = team
            try:
                record.save()
                return redirect('single-physical-assessment', pk=team.id, papk=physical_assessment.id)
            except IntegrityError:
                form.add_error(None, _("A record with this Physical Assessment, Team, and Date already exists."))
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))
    context = {'teamObj': team, 'role':role, 'form': form, 'pa': physical_assessment}
    return render(request, 'teams/create_physical_assessment_record.html', context)


@login_required(login_url="login")
@user_is_member_and_have_access
def editPhysicalAssessmentMeasurement(request, pk, papk, recordid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    
    # Use select_related to reduce number of queries
    physical_assessment = get_object_or_404(PhysicalAssessment.objects.select_related('team'), id=papk, team=pk)
    physical_assessment_measurement = get_object_or_404(PhysicalAssessmentRecord.objects.select_related('team', 'physical_assessment'), id=recordid, team=pk, physical_assessment=papk)

    pa_score_records = PhysicalAssessmentScore.objects.select_related(
        'team_member__profileID'
        ).filter(
            physical_assessment=physical_assessment,
            physical_assessment_record=recordid,
            team=team,
            team_member__is_active=True,
        )
    PaScoreRecordsFormSet = modelformset_factory(PhysicalAssessmentScore, form=PhysicalAssessmentScoreForm, extra=0)
    formset = PaScoreRecordsFormSet(queryset=pa_score_records)
    if request.method == 'POST':
        formset = PaScoreRecordsFormSet(request.POST, queryset=pa_score_records)
        if formset.is_valid():
            try:
                formset.save()
                return redirect('single-physical-assessment', pk=team.id, papk=physical_assessment.id)
            except IntegrityError:
                messages.error(request, _('An error has occurred due to a unique constraint violation.'))
        else:
            messages.error(request, _('An error has occurred editing attendance'))
    context = {
        'teamObj': team,
        'pa_score_records': pa_score_records,
        'formset': formset,
        'role': role,
        'pa_record': physical_assessment,
        'pa_measurement': physical_assessment_measurement,
    }
    return render(request, 'teams/physical_assessment_score.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def deletePhysicalAssessmentMeasurements(request, pk, papk, recordid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    record = get_object_or_404(PhysicalAssessmentRecord, id=recordid, team=team.id, physical_assessment=papk)
    if request.method == 'POST':
        record.delete()
        return redirect('single-physical-assessment', pk=team.id, papk=record.physical_assessment.id)
    context = {'teamObj': team, 'role':role, 'record': record}
    return render(request, 'teams/deletetemplates/delete_physical_assessment_record.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def downloadPhysicalAssessmentScore(request, pk, papk):
    team = request.team
    
    physical_assessment = get_object_or_404(
        PhysicalAssessment.objects.select_related('team'),
        id=papk,
        team=team.id
    )

    physical_assessment_scores = PhysicalAssessmentScore.objects.filter(
        physical_assessment=physical_assessment,
        team=team,
        team_member__is_active=True
    ).prefetch_related(
        Prefetch('team_member', queryset=TeamMember.objects.select_related('profileID'))
    ).select_related('physical_assessment_record')

    scores_by_member_and_date = defaultdict(lambda: defaultdict(lambda: None))
    dates = PhysicalAssessmentScore.objects.filter(
        physical_assessment=physical_assessment,
        team=team,
        team_member__is_active=True,
    ).values_list('physical_assessment_record__physical_assessment_date', flat=True).distinct()

    for score in physical_assessment_scores:
        scores_by_member_and_date[score.team_member][score.physical_assessment_record.physical_assessment_date] = score

    sorted_dates = sorted(list(dates))
    team_members = scores_by_member_and_date.keys()

    # Create a response object with the appropriate content type for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{physical_assessment.team.teamName}_{physical_assessment.physical_assessment_title}_{physical_assessment.assessment_type}_results.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

     # Write the header row with attribute names and formatted dates
    header_row = ["athlete"] + [date.strftime('%d.%m.%y') for date in sorted_dates]
    writer.writerow(header_row)

    # Write the data rows
    for team_member in team_members:
        data_row = [team_member.profileID.name]
        for date in sorted_dates:
            score = scores_by_member_and_date[team_member][date]
            
            # Choose the correct field based on the assessment type
            assessment_type = physical_assessment.assessment_type
            if assessment_type == 'score':
                value_to_append = score.score if score and score.score is not None else ""
            elif assessment_type == 'time':
                value_to_append = score.time if score and score.time is not None else ""
            elif assessment_type == 'distance':
                value_to_append = score.distance if score and score.distance is not None else ""
            else:
                # Handle any other cases or default to an empty string
                value_to_append = ""

            data_row.append(str(value_to_append))  # Convert to string
        writer.writerow(data_row)

    
    return response

@login_required(login_url="login")
@user_is_member_and_have_access
def addTeamMemberToPhysicalAssessmentMeasurement(request, pk, papk, recordid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    
    # prefetch_related is used to efficiently fetch many-to-many and reverse foreign key relationships
    team_members = team.teammember_set.select_related('profileID').filter(role=1, is_active=True).order_by('profileID__name')

    pa_record = get_object_or_404(PhysicalAssessmentRecord, id=recordid, team=team.id, physical_assessment=papk)
    
    form = AddTeamMemberScoreToPhysicalAssessmentRecord(team_members=team_members)
    context = {'teamObj': team, 'role': role, 'form': form, 'pa_record': pa_record}

    if request.method == 'POST':
        userId = request.POST.get('team_member')
        if not userId or userId == None:
            messages.error(request, _("Please select a team member"))
            return render(request, 'teams/add-teammember-to-Physical-Assessment-Record.html', context)

        selectedTeamMember = TeamMember.objects.filter(profileID=userId, teamID=team.id, is_active=True).first()

        if not selectedTeamMember:
            messages.error(request, _("You can't add a user who is not a team member"))
        elif PhysicalAssessmentScore.objects.filter(physical_assessment_record=pa_record, physical_assessment=papk, team_member=selectedTeamMember, team_member__is_active=True).exists():
            messages.error(request, _("Team member already have score, for this physical assessment record"))
        else:
            assessment_type = pa_record.physical_assessment.assessment_type
            if assessment_type == 'score':
                createMemberPhysicalAssessmentScore = PhysicalAssessmentScore.objects.create(
                    team_member=selectedTeamMember,
                    physical_assessment=pa_record.physical_assessment,
                    physical_assessment_record=pa_record,
                    team=team,
                    score=0,  
                )
            elif assessment_type == 'time':
                createMemberPhysicalAssessmentScore = PhysicalAssessmentScore.objects.create(
                    team_member=selectedTeamMember,
                    physical_assessment=pa_record.physical_assessment,
                    physical_assessment_record=pa_record,
                    team=team,
                    time=timedelta(),  
                )
            elif assessment_type == 'distance':
                createMemberPhysicalAssessmentScore = PhysicalAssessmentScore.objects.create(
                    team_member=selectedTeamMember,
                    physical_assessment=pa_record.physical_assessment,
                    physical_assessment_record=pa_record,
                    team=team,
                    distance=0, 
                )
            else:
                messages.error(request, _("Server Error occured "))
                return redirect('edit-physical-assessment-measurement', pk=team.id, papk=pa_record.physical_assessment.id, recordid=pa_record.id)
            createMemberPhysicalAssessmentScore.save()
            return redirect('edit-physical-assessment-measurement', pk=team.id, papk=pa_record.physical_assessment.id, recordid=pa_record.id)

    return render(request, 'teams/add-teammember-to-Physical-Assessment-Record.html', context)
    
@login_required(login_url="login")
@user_is_member_and_have_access
def deleteTeamMemberPhysicalAssessmentMeasurement(request, pk, papk, recordid, memberid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    record = get_object_or_404(PhysicalAssessmentScore, id=recordid, team=team.id, physical_assessment=papk, team_member=memberid )
    if request.method == 'POST':
        record.delete()
        return redirect('edit-physical-assessment-measurement', pk=team.id, papk=record.physical_assessment.id, recordid=record.physical_assessment_record.id)
    context = {'teamObj': team, 'role':role, 'record': record}
    return render(request, 'teams/deletetemplates/delete_teammember_physical_assessment_measurement.html', context)

# Team Organization PhysicalAssessment

@login_required(login_url="login")
@user_is_team_member
def organizationSinglePhysicalAssessment(request, pk, opaid):
    team = request.team
    role = request.member.role
    organization = team.organization.id
    org_physical_assessment = get_object_or_404(
        OrganizationPhysicalAssessment.objects.select_related('organization'),
        id=opaid,
    )

    org_physical_assessment_records = OrganizationPhysicalAssessmentRecord.objects.filter(
        org_physical_assessment=org_physical_assessment,
        team=team,
        organization=organization
    ).only('org_physical_assessment_date').order_by('org_physical_assessment_date')

    org_physical_assessment_scores = OrganizationPhysicalAssessmentScore.objects.filter(
        org_physical_assessment=org_physical_assessment,
        team=team,
        organization=organization,
        team_member__is_active=True
    ).prefetch_related(
        Prefetch('team_member', queryset=TeamMember.objects.select_related('profileID'))
    ).select_related('org_physical_assessment_record')

    scores_by_member_and_date = defaultdict(lambda: defaultdict(lambda: None))
    dates = OrganizationPhysicalAssessmentScore.objects.filter(
        org_physical_assessment=org_physical_assessment,
        team=team,
        organization=organization,
        team_member__is_active=True
    ).values_list('org_physical_assessment_record__org_physical_assessment_date', flat=True).distinct()
  
    for score in org_physical_assessment_scores:
        scores_by_member_and_date[score.team_member][score.org_physical_assessment_record.org_physical_assessment_date] = score

    sorted_dates = sorted(list(dates))
    team_members = scores_by_member_and_date.keys()

    
    form = OrgPhysicalAssessmentChoiceForm(request.POST or None, parecords=org_physical_assessment_records)
    
    if request.method == 'POST' and form.is_valid():
        selected_date = form.cleaned_data['pa_dates']
        if selected_date:
            return redirect('edit-org-physical-assessment-measurement', pk=team.id, opaid=selected_date.org_physical_assessment.id, recordid=selected_date.id)
    

    context = {
        'teamObj': team,
        'record': org_physical_assessment,
        'role': role,
        'parecords': org_physical_assessment_records,
        'pa_score': org_physical_assessment_scores,
        'team_members': team_members,
        'form': form,
        'dates': sorted_dates,
        'scores_by_member_and_date': scores_by_member_and_date
    }
    return render(request, 'teams/org_physical_assessments_single.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def organizationNewPhysicalAssessmentMeasurement(request, pk, opaid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    org=team.organization
    org_physical_assessment = get_object_or_404(OrganizationPhysicalAssessment, id=opaid, organization=org)

    form = OrgPhysicalAssessmentRecordForm()
    if request.method == 'POST':
        form = OrgPhysicalAssessmentRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.org_physical_assessment = org_physical_assessment
            record.team = team
            record.organization = org
            try:
                record.save()
                return redirect('org-single-physical-assessment', pk=team.id, opaid=org_physical_assessment.id)
            except IntegrityError:
                form.add_error(None, _("A record with this Physical Assessment, Team, Organization and Date already exists."))
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))
    context = {'teamObj': team, 'role':role, 'form': form, 'pa': org_physical_assessment}
    return render(request, 'teams/org_create_physical_assessment_record.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def organizationEditPhysicalAssessmentMeasurement(request, pk, opaid, recordid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    organization = team.organization.id
    
    # Use select_related to reduce number of queries
    org_physical_assessment = get_object_or_404(OrganizationPhysicalAssessment.objects.select_related('organization'), id=opaid, organization=organization)
    org_physical_assessment_measurement = get_object_or_404(OrganizationPhysicalAssessmentRecord.objects.select_related('team', 'organization', 'org_physical_assessment'), id=recordid, team=pk, org_physical_assessment=org_physical_assessment.id)

    pa_score_records = OrganizationPhysicalAssessmentScore.objects.select_related(
        'team_member__profileID'
        ).filter(
            org_physical_assessment=org_physical_assessment.id,
            org_physical_assessment_record=recordid,
            team=team.id,
            organization=organization,
            team_member__is_active=True,
        )
    PaScoreRecordsFormSet = modelformset_factory(OrganizationPhysicalAssessmentScore, form=OrgPhysicalAssessmentScoreForm, extra=0)
    formset = PaScoreRecordsFormSet(queryset=pa_score_records)
    if request.method == 'POST':
        formset = PaScoreRecordsFormSet(request.POST, queryset=pa_score_records)
        if formset.is_valid():
            try:
                formset.save()
                return redirect('org-single-physical-assessment', pk=team.id, opaid=org_physical_assessment.id)
            except IntegrityError:
                messages.error(request, _('An error has occurred due to a unique constraint violation.'))
        else:
            messages.error(request, _('An error has occurred editing attendance'))
    context = {
        'teamObj': team,
        'pa_score_records': pa_score_records,
        'formset': formset,
        'role': role,
        'pa_record': org_physical_assessment,
        'pa_measurement': org_physical_assessment_measurement,
    }
    return render(request, 'teams/org_physical_assessment_score.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def organizationDeletePhysicalAssessmentMeasurements(request, pk, opaid, recordid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    organization = team.organization
    record = get_object_or_404(OrganizationPhysicalAssessmentRecord, id=recordid, team=team, org_physical_assessment=opaid, organization=organization)
    if request.method == 'POST':
        record.delete()
        return redirect('org-single-physical-assessment', pk=team.id, opaid=record.org_physical_assessment.id)
    context = {'teamObj': team, 'role':role, 'record': record}
    return render(request, 'teams/deletetemplates/delete_org_physical_assessment_record.html', context)


@login_required(login_url="login")
@user_is_member_and_have_access
def organizationAddTeamMemberToPhysicalAssessmentMeasurement(request, pk, opaid, recordid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    organization = team.organization.id
    # prefetch_related is used to efficiently fetch many-to-many and reverse foreign key relationships
    team_members = team.teammember_set.select_related('profileID').filter(role=1, is_active=True).order_by('profileID__name')

    pa_record = get_object_or_404(OrganizationPhysicalAssessmentRecord, id=recordid, team=team.id, org_physical_assessment=opaid)
    
    form = AddTeamMemberScoreToPhysicalAssessmentRecord(team_members=team_members)
    context = {'teamObj': team, 'role': role, 'form': form, 'pa_record': pa_record}

    if request.method == 'POST':
        userId = request.POST.get('team_member')
        if not userId or userId == None:
            messages.error(request, _("Please select a team member"))
            return render(request, 'teams/org-add-teammember-to-Physical-Assessment-Record.html', context)

        selectedTeamMember = TeamMember.objects.filter(profileID=userId, teamID=team.id, is_active=True).first()

        if not selectedTeamMember:
            messages.error(request, _("You can't add a user who is not a team member"))
        elif OrganizationPhysicalAssessmentScore.objects.filter(org_physical_assessment_record=pa_record, org_physical_assessment=opaid, team_member=selectedTeamMember).exists():
            messages.error(request, _("Team member already have score, for this physical assessment record"))
        else:
            assessment_type = pa_record.org_physical_assessment.assessment_type
            if assessment_type == 'score':
                createMemberPhysicalAssessmentScore = OrganizationPhysicalAssessmentScore.objects.create(
                    team_member=selectedTeamMember,
                    org_physical_assessment=pa_record.org_physical_assessment,
                    org_physical_assessment_record=pa_record,
                    organization=team.organization,
                    team=team,
                    score=0,  
                )
            elif assessment_type == 'time':
                createMemberPhysicalAssessmentScore = OrganizationPhysicalAssessmentScore.objects.create(
                    team_member=selectedTeamMember,
                    org_physical_assessment=pa_record.org_physical_assessment,
                    org_physical_assessment_record=pa_record,
                    organization=team.organization,
                    team=team,
                    time=timedelta(),  
                )
            elif assessment_type == 'distance':
                createMemberPhysicalAssessmentScore = OrganizationPhysicalAssessmentScore.objects.create(
                    team_member=selectedTeamMember,
                    org_physical_assessment=pa_record.org_physical_assessment,
                    org_physical_assessment_record=pa_record,
                    organization=team.organization,
                    team=team,
                    distance=0, 
                )
            else:
                messages.error(request, _("Server Error occured "))
                return redirect('edit-org-physical-assessment-measurement', pk=team.id, opaid=pa_record.org_physical_assessment.id, recordid=pa_record.id)
            createMemberPhysicalAssessmentScore.save()
            return redirect('edit-org-physical-assessment-measurement', pk=team.id, opaid=pa_record.org_physical_assessment.id, recordid=pa_record.id)

    return render(request, 'teams/org-add-teammember-to-Physical-Assessment-Record.html', context)

@login_required(login_url="login")
@user_is_owner
def organizationDeleteTeamMemberPhysicalAssessmentMeasurement(request, pk, opaid, recordid, memberid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    organization = team.organization.id
    role = current_user_member.role
    record = get_object_or_404(OrganizationPhysicalAssessmentScore, id=recordid, team=team.id, org_physical_assessment=opaid, team_member=memberid, organization=organization )
    if request.method == 'POST':
        record.delete()
        return redirect('edit-org-physical-assessment-measurement', pk=team.id, opaid=record.org_physical_assessment.id, recordid=record.org_physical_assessment_record.id)
    context = {'teamObj': team, 'role':role, 'record': record}
    return render(request, 'teams/deletetemplates/delete_org_teammember_physical_assessment_measurement.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def downloadOrganizationPhysicalAssessmentScore(request, pk, opaid):
    team = request.team
    organization = team.organization.id
    teamname = team.teamName

    org_physical_assessment = get_object_or_404(
        OrganizationPhysicalAssessment.objects.select_related('organization'),
        id=opaid,
        organization=organization
    )

    physical_assessment_scores = OrganizationPhysicalAssessmentScore.objects.filter(
        org_physical_assessment=org_physical_assessment,
        team=team,
        organization=organization,
        team_member__is_active=True,
    ).prefetch_related(
        Prefetch('team_member', queryset=TeamMember.objects.select_related('profileID'))
    ).select_related('org_physical_assessment_record')

    scores_by_member_and_date = defaultdict(lambda: defaultdict(lambda: None))
    dates = OrganizationPhysicalAssessmentScore.objects.filter(
        org_physical_assessment=org_physical_assessment,
        team=team,
        organization=organization,
        team_member__is_active=True,
    ).values_list('org_physical_assessment_record__org_physical_assessment_date', flat=True).distinct()

    for score in physical_assessment_scores:
        scores_by_member_and_date[score.team_member][score.org_physical_assessment_record.org_physical_assessment_date] = score

    sorted_dates = sorted(list(dates))
    team_members = scores_by_member_and_date.keys()

    # Create a response object with the appropriate content type for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{org_physical_assessment.organization.name}_{teamname}_{org_physical_assessment.opa_title}_{org_physical_assessment.assessment_type}_results.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

     # Write the header row with attribute names and formatted dates
    header_row = ["athlete"] + [date.strftime('%d.%m.%y') for date in sorted_dates]
    writer.writerow(header_row)

    # Write the data rows
    for team_member in team_members:
        data_row = [team_member.profileID.name]
        for date in sorted_dates:
            score = scores_by_member_and_date[team_member][date]
            
            # Choose the correct field based on the assessment type
            assessment_type = org_physical_assessment.assessment_type
            if assessment_type == 'score':
                value_to_append = score.score if score and score.score is not None else ""
            elif assessment_type == 'time':
                value_to_append = score.time if score and score.time is not None else ""
            elif assessment_type == 'distance':
                value_to_append = score.distance if score and score.distance is not None else ""
            else:
                # Handle any other cases or default to an empty string
                value_to_append = ""

            data_row.append(str(value_to_append))  # Convert to string
        writer.writerow(data_row)

    
    return response

# PLAYBOOK

@login_required(login_url="login")
@user_is_team_member
def viewTactics(request, pk):
    team = request.team
    role = request.member.role

    # Fetch tactics based on the role
    if role in ('1', '3'):
        tactics = TeamTactic.objects.filter(team=team.id, public=True).select_related('owner').order_by('title')
    else:
        tactics = TeamTactic.objects.filter(team=team.id).select_related('owner').order_by('title')

    context = {'teamObj': team, 'role': role, 'tactics': tactics}
    return render(request, 'teams/team-tactics.html', context)

@login_required(login_url="login")
@user_is_team_member
def viewSingleTactic(request, pk, tid):
    team = request.team
    current_user = request.member
    role = current_user.role

    tactic = get_object_or_404(TeamTactic, id=tid, team=team.id)
    images = tactic.tactic_images.all().order_by('play')  # Get all TacticImage instances related to this TeamTactic

    context = {'teamObj': team, 'role': role, 'tactic': tactic, 'images': images}
    return render(request, 'teams/team-single-tactic.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access    
def add_team_tactic(request, pk):
        team = request.team
        current_user_member = request.current_user_member
        role = current_user_member.role

        if request.method == 'POST':
            form = TacticForm(request.POST)
            if form.is_valid():
                tactic = form.save(commit=False)
                tactic.team = team
                tactic.owner = current_user_member.profileID
                tactic.save()
            return redirect('view-tactic', pk=team.id, tid=tactic.id)
        else:
            form = TacticForm()
        context = {'form': form, 'role': role, 'teamObj': team}
        return render(request, 'teams/add_team_tactic.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def editTactic(request, pk, tid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    tactic = get_object_or_404(TeamTactic, id=tid, team=pk)
    if current_user_member.profileID != tactic.owner:
        return redirect('view-tactic', pk=team.id, tid=tactic.id)
    if request.method == 'POST':
        form = TacticForm(request.POST, instance=tactic)
        if form.is_valid():
            tactic = form.save(commit=False)
            tactic.team = team
            tactic.owner = current_user_member.profileID
            tactic.save()
            return redirect('view-tactic', pk=team.id, tid=tactic.id)
    else:
        form = TacticForm(instance=tactic)
    context = {'form': form, 'role': role, 'teamObj': team, 'tactic': tactic}
    return render(request, 'teams/edit_team_tactic.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access  
def editTacticPlays(request, pk, tid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    tactic = get_object_or_404(TeamTactic, id=tid, team=team.id)
    if current_user_member.profileID != tactic.owner:
        return redirect('view-tactic', pk=team.id, tid=tactic.id)
    # Order the images by 'play' here:
    images = tactic.tactic_images.all().order_by('play')

    # Create a formset for the TacticImage model
    domain = 'https://'+ settings.AWS_S3_CUSTOM_DOMAIN
    TacticImageFormSet = modelformset_factory(TacticImage, form=TacticImageForm, extra=0)
    if request.method == "POST":
        formset = TacticImageFormSet(request.POST, request.FILES, queryset=images)
        if formset.is_valid():
            formset.save()
            return redirect('edit-tactic-plays', pk=pk, tid=tid)
    else:
        formset = TacticImageFormSet(queryset=images)

    is_empty = not bool(formset.total_form_count())

    context = {'teamObj': team, 'role': role, 'tactic': tactic, 'formset': formset, 'is_empty': is_empty, 'domain': domain}
    return render(request, 'teams/edit-tactic-plays.html', context)


@login_required(login_url="login")
@user_is_member_and_have_access    
def deleteTactic(request, pk, tid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    # Make sure to fetch the owner in the same query.
    tactic = get_object_or_404(TeamTactic.objects.select_related('owner'), id=tid, team=pk)
    
    if current_user_member.profileID != tactic.owner and current_user_member.profileID != team.owner:
        return redirect('view-tactic', pk=team.id, tid=tactic.id)
    
    if request.method == 'POST':
        tactic.delete()
        return redirect('view-playbook', pk=team.id)
    
    context = {'teamObj': team, 'object': tactic, 'role': role}
    return render(request, 'teams/deletetemplates/delete_team_tactic.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access    
def upload_tactic_play(request, pk, tid): # tactic single image upload
    team = request.team
    team_tactic = get_object_or_404(TeamTactic, id=tid, team=team.id)

    current_user_member = request.current_user_member
    role = current_user_member.role
    form = TacticImageForm()

    if request.method == 'POST':
        form = TacticImageForm(request.POST, request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.team_tactic = team_tactic
            instance.save()

            return redirect('edit-tactic-plays', pk=team.id, tid=team_tactic.id)  # Or wherever you want to redirect after successful upload
        

    context = {'teamObj': team, 'form': form, 'role': role, 'tactic': team_tactic}
    return render(request, 'teams/upload_tactic_play.html', context)



@login_required(login_url="login")
@user_is_member_and_have_access    
def deleteTacticPlay(request, pk, tid, pid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    tacticPlay = get_object_or_404(TacticImage, id=pid, team_tactic=tid)

    if request.method == 'POST':
        tacticPlay.delete()
        return redirect('edit-tactic-plays', pk=team.id, tid=tacticPlay.team_tactic.id)
    context = {'teamObj': team, 'object': tacticPlay, 'role':role}
    return render(request, 'teams/deletetemplates/delete_tactic_play.html', context)

@login_required(login_url="login")
@user_is_member_and_have_access
def drawNewTactic(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role

    context = {
        'teamObj': team,
        'role': role,
    }
    return render(request, 'teams/canvas.html', context)


# ANALYTICS

@login_required(login_url="login")
@user_is_team_member
def teamAnalytics(request, pk):
    team = request.team
    current_user = request.member
    role = current_user.role

    team_season_form = TeamSeasonForm(request.POST or None, team=team)
    date_form = TeamAnalyticsDateForm(request.POST or None)
    start_datetime = None
    end_datetime = None
    team_season = None

    # Get the current timezone
    current_timezone = timezone.get_current_timezone()

    if request.method == 'POST':
        if 'team_season' in request.POST and team_season_form.is_valid():
            team_season = team_season_form.cleaned_data['team_season']
            # Convert the team season start and end date to DateTime objects
            start_datetime = timezone.make_aware(timezone.datetime.combine(team_season.start_date, time.min), timezone=current_timezone)
            end_datetime = timezone.make_aware(timezone.datetime.combine(team_season.end_date, time.max), timezone=current_timezone)
            
        elif 'start_date' in request.POST and 'end_date' in request.POST and date_form.is_valid():
            if date_form.is_date_valid('start_date') and date_form.is_date_valid('end_date'):
                start_date = date_form.cleaned_data['start_date']
                end_date = date_form.cleaned_data['end_date']
                # Convert the start_date and end_date to DateTime objects
                start_datetime = timezone.make_aware(timezone.datetime.combine(start_date, time.min), timezone=current_timezone)
                end_datetime = timezone.make_aware(timezone.datetime.combine(end_date, time.max), timezone=current_timezone)
            else:
                messages.error(request, _("Please enter valid start and end date."))
                return redirect('team-analytics', pk=team.id)
    elif not start_datetime and not end_datetime:  # If no team season is active and no dates are submitted
        # Get the current month's start and end date
        today = timezone.now()
        start_datetime = timezone.make_aware(timezone.datetime(today.year, today.month, 1), timezone=current_timezone)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_datetime = timezone.make_aware(timezone.datetime(today.year, today.month, last_day, 23, 59, 59), timezone=current_timezone)
 

    team_attendance = team.attendancerecord_set.filter(team=team.id, event__start_time__range=(start_datetime, end_datetime), team_member__is_active=True)
    team_events = team.events.filter(teamID=team.id, start_time__range=(start_datetime, end_datetime))
    attendance_data = generate_attendance_data(team_attendance)
    team_members_data, gender_count  = generate_team_members_data(team, team_season,start_datetime, end_datetime)
    event_data = generate_event_data(team_events)
    happened_event_data = generate_happened_event_data(team_events, team_attendance)
    filter_date_range = {
        'start_date': start_datetime,
        'end_date': end_datetime
    }


    context = {
        'teamObj': team,
        'role': role,
        'team_events': team_events,
        'event_data': event_data,
        'team_attendance': team_attendance,
        'attendance_data': attendance_data,
        'team_members_data': team_members_data,
        'happened_event_data': happened_event_data,
        'team_season_form': team_season_form,
        'date_form': date_form,
        'filter_date': filter_date_range,
        'gender_count': gender_count,
    }

    return render(request, 'teams/team-analytics.html', context)


#  Analytics for team member
@login_required(login_url="login")
@user_is_team_member
def teamMemberAnalytics(request, pk, mpk):
    team = request.team
    current_user = request.member
    role = current_user.role

    # mpk = TeamMember ID
    team_member = get_object_or_404(TeamMember, id=mpk, teamID=team.id, is_active=True)

    team_season_form = TeamSeasonForm(request.POST or None, team=team)
    date_form = TeamAnalyticsDateForm(request.POST or None)
    start_datetime = None
    end_datetime = None
    team_season = None
    # Get the current timezone
    current_timezone = timezone.get_current_timezone()

    if request.method == 'POST':
        if 'team_season' in request.POST and team_season_form.is_valid():
            team_season = team_season_form.cleaned_data['team_season']
            # Convert the team season start and end date to DateTime objects
            start_datetime = timezone.make_aware(timezone.datetime.combine(team_season.start_date, time.min), timezone=current_timezone)
            end_datetime = timezone.make_aware(timezone.datetime.combine(team_season.end_date, time.max), timezone=current_timezone)
            
        elif 'start_date' in request.POST and 'end_date' in request.POST and date_form.is_valid():
            if date_form.is_date_valid('start_date') and date_form.is_date_valid('end_date'):
                start_date = date_form.cleaned_data['start_date']
                end_date = date_form.cleaned_data['end_date']
                # Convert the start_date and end_date to DateTime objects
                start_datetime = timezone.make_aware(timezone.datetime.combine(start_date, time.min), timezone=current_timezone)
                end_datetime = timezone.make_aware(timezone.datetime.combine(end_date, time.max), timezone=current_timezone)
            else:
                messages.error(request, _("Please enter valid start and end date."))
                return redirect('team-analytics', pk=team.id)
    elif not start_datetime and not end_datetime:  # If no team season is active and no dates are submitted
        # Get the current month's start and end date
        today = timezone.now()
        start_datetime = timezone.make_aware(timezone.datetime(today.year, today.month, 1), timezone=current_timezone)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_datetime = timezone.make_aware(timezone.datetime(today.year, today.month, last_day, 23, 59, 59), timezone=current_timezone)
 


    team_member_attendance = team.attendancerecord_set.filter(
        team=team.id, team_member=team_member, team_member__is_active=True, event__start_time__range=(start_datetime, end_datetime)
    ).select_related('event')

    physical_assessment_scores = PhysicalAssessmentScore.objects.filter(
        team_member=team_member,
        team=team.id,
        team_member__is_active=True
    ).select_related('physical_assessment', 'physical_assessment_record').order_by('physical_assessment__physical_assessment_title', '-physical_assessment_record__physical_assessment_date')
 
    org_physical_assessment_scores = OrganizationPhysicalAssessmentScore.objects.filter(
        team_member=team_member,
        team=team.id,
        team_member__is_active=True
    ).select_related('org_physical_assessment', 'org_physical_assessment_record').order_by('org_physical_assessment__opa_title', '-org_physical_assessment_record__org_physical_assessment_date')

    team_member_attendance_with_value = team_member_attendance.exclude(
        attendance=AttendanceRecord.EMPTYVALUE
    )


    member_attendance_data = generate_attendance_data(team_member_attendance)
    happened_event_data = generate_happened_athlete_event_data(team_member_attendance, team_member_attendance_with_value)
    attendance_data = generate_teammember_attendace_data(team_member_attendance)
    filter_date_range = {
        'start_date': start_datetime,
        'end_date': end_datetime
    }

    context = {
        'teamObj': team,
        'role': role,
        'team_season_form': team_season_form,
        'date_form': date_form,
        'team_member': team_member,
        'attendance_data': attendance_data,
        'member_attendance_data': member_attendance_data,
        'attendance_records': team_member_attendance,
        'happened_event_data': happened_event_data,
        'physical_assessment_scores': physical_assessment_scores,
        'org_physical_assessment_scores': org_physical_assessment_scores,
        'filter_date': filter_date_range,
    }

    return render(request, 'teams/team-analytics-member.html', context)


#  SEASON


@login_required(login_url="login")
@user_is_member_and_have_access
def createTeamSeason(request, pk):
    page = "CREATE"
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    form = SingleTeamSeasonForm()

    if request.method == 'POST':
        form = SingleTeamSeasonForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            if end_date < start_date:
                messages.error(request, _('End date cannot be before the start date'))
            else:
                season = form.save(commit=False)
                season.team = team
                season.save()
                messages.success(request, _('New season Added!'))
                return redirect('team-seasons', pk=team.id)
        
    context = {'teamObj': team, 'role': role, 'form': form, 'page': page}
    return render(request, 'teams/create_season.html', context)

@login_required(login_url="login")
@user_is_owner
def viewTeamSeasons(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role

    seasons = TeamSeason.objects.filter(team=pk).order_by('-current_season', 'start_date')
    context = {'teamObj': team, 'role':role, 'seasons': seasons}
    return render(request, 'teams/team_seasons.html', context)



@login_required(login_url="login")
@user_is_owner
def editTeamSeason(request, pk, sid):
    page = "EDIT"
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    season = get_object_or_404(TeamSeason, id=sid, team=pk)
    form = SingleTeamSeasonForm(instance=season)
    if request.method == 'POST':
        form = SingleTeamSeasonForm(request.POST,instance=season)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            if end_date < start_date:
                messages.error(request, _('End date cannot be before the start date'))
            else:
                teamSeason = form
                teamSeason.save()
                messages.success(request, _('Season updated!'))
                return redirect('team-seasons', pk=team.id)
    context = {'teamObj': team, 'form': form , 'role': role, 'page': page }         
    return render(request, 'teams/create_season.html',context)

@login_required(login_url="login")
@user_is_owner
def deleteTeamSeason(request, pk, sid):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role

    season = get_object_or_404(TeamSeason, id=sid, team=pk)

    if request.method == 'POST':
        season.delete()
        return redirect('team-seasons', pk=team.id)
    context = {'teamObj': team, 'object': season, 'role':role}
    return render(request, 'teams/deletetemplates/delete_team_season.html', context)


@login_required(login_url="login")
@user_is_owner
def createEmailNotification(request, pk):
    page = "CREATE"
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    # Pass team_id when initializing the form
    form = EmailNotificationForm(team_id=team.id)

    if request.method == 'POST':
        form = EmailNotificationForm(request.POST, team_id=team.id)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.team = team
            notification.save()
            form.save_m2m()  # This is the correct usage
            messages.success(request, _('New notification template created!'))
            return redirect('email-notifications', pk=team.id)
    
    context = {'teamObj': team, 'role': role, 'form': form, 'page': page}
    return render(request, 'teams/email_notification_form.html', context)


@login_required(login_url="login")
@user_is_owner
def editEmailNotification(request, pk, nid):
    page = "EDIT"
    team = request.team
    notification = get_object_or_404(TeamNotification, team=team, id=nid)

    if request.method == 'POST':
        # Initialize the form with POST data, instance, and team_id
        form = EmailNotificationForm(request.POST, instance=notification, team_id=team.id)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.team = team
            notification.save()
            form.save_m2m()  # Save many-to-many data for the links
            messages.success(request, _('Notification template was updated!'))
            return redirect('email-notifications', pk=team.id)
    else:
        # Initialize the form with instance and team_id for GET request
        form = EmailNotificationForm(instance=notification, team_id=team.id)

    context = {'teamObj': team, 'form': form, 'page': page}
    return render(request, 'teams/email_notification_form.html', context)

@login_required(login_url="login")
@user_is_owner
def deleteEmailNotification(request, pk, nid):

    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    notification = get_object_or_404(TeamNotification, id=nid, team=pk)

    if request.method == 'POST':
        notification.delete()
        messages.warning(request, _('Notification deleted!'))
        return redirect('email-notifications', pk=team.id)
    context = {'teamObj': team, 'object': notification, 'role':role}
    return render(request, 'teams/deletetemplates/delete_team_notification.html', context)


@login_required(login_url="login")
@user_is_owner
def allEmailNotifications(request, pk):

    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    team_notifications = TeamNotification.objects.filter(team=team)

    
    context = {'teamObj': team, 'role': role, 'notifications': team_notifications}
    return render(request, 'teams/email_notifications_all.html', context)

# TEAM LINKS

@login_required(login_url="login")
@user_is_owner
def allTeamLinks(request, pk):

    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    team_links = NotificationLink.objects.filter(team=team)

    
    context = {'teamObj': team, 'role': role, 'links': team_links}
    return render(request, 'teams/notifications_links_all.html', context)


@login_required(login_url="login")
@user_is_owner
def createTeamLink(request, pk):
    page = "CREATE"
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    form = TeamNotificationLinkForm()
    if request.method == 'POST':
        form = TeamNotificationLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.team = team
            link.save()
            messages.success(request, _('New link created!'))
            return redirect('team-notification-links', pk=team.id)

    context = {'teamObj': team, 'role': role, 'form': form, 'page': page}
    return render(request, 'teams/notifications_links_form.html', context)

@login_required(login_url="login")
@user_is_owner
def editTeamLink(request, pk, lid):
    page = "EDIT"
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role
    link = get_object_or_404(NotificationLink,  team=team, id=lid)
    form = TeamNotificationLinkForm(instance=link)

    if request.method == 'POST':
        form = TeamNotificationLinkForm(request.POST,instance=link)
        if form.is_valid():
            link = form.save(commit=False)
            link.save()
            messages.success(request, _('Link was updated!'))
            return redirect('team-notification-links', pk=team.id)
    
    # If the form is not valid, include the errors in the context
    context = {'teamObj': team, 'role': role, 'form': form, 'page': page}
    return render(request, 'teams/notifications_links_form.html', context)

@login_required(login_url="login")
@user_is_owner
def deleteTeamLink(request, pk, lid):
    team = request.team
    current_user_member = request.current_user_member
    role = current_user_member.role

    link = get_object_or_404(NotificationLink, id=lid, team=pk)

    if request.method == 'POST':
        link.delete()
        messages.warning(request, _('Link was deleted!'))
        return redirect('team-notification-links', pk=team.id)
    context = {'teamObj': team, 'object': link, 'role':role}
    return render(request, 'teams/deletetemplates/delete_team_link.html', context)


# TEAM SETTINGS

@login_required(login_url="login")
@user_is_owner
def teamSettings(request, pk):
    team = request.team
    current_user_member = request.current_user_member
    if current_user_member is None:
        return redirect('teams')
    role = current_user_member.role
    form = TeamForm(instance=team)
    oldimage = team.team_image
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            team_image = form.cleaned_data['team_image']

            # Resize image only if a new image is uploaded
            if team_image and team_image != oldimage:
                # Read the image data from the uploaded file
                img_data = team_image.read()
                # Open the image using Pillow
                img = Image.open(BytesIO(img_data))

                # Get the original width and height
                width, height = img.size

                # Calculate the new maximum dimension to maintain aspect ratio
                max_size = 350
                new_width = max_size
                new_height = max_size

                if width > height:
                    # Landscape image, adjust height based on width
                    new_height = int((height * new_width) / width)
                else:
                    # Portrait image, adjust width based on height
                    new_width = int((width * new_height) / height)

                # Resize the image
                img = img.resize((new_width, new_height), Image.LANCZOS)

                # Create a new in-memory file-like object to store the resized image
                resized_img_data = BytesIO()
                img.save(resized_img_data, format=img.format or 'JPEG')

                # Reset the uploaded image data with the resized data
                team_image.seek(0)
                team_image.write(resized_img_data.getvalue())
            form.save()
            return redirect('team', pk=team.id)
    domain = 'https://'+ settings.AWS_S3_CUSTOM_DOMAIN
    
    context = {
        'teamObj': team,
        'role': role,
        'form': form,
        'domain': domain,
    }
    return render(request, 'teams/team-settings.html', context)


# LEAVE TEAM

@login_required(login_url="login")
@user_is_team_member
def leaveTeam(request, pk):
    team = request.team

    # Check if the user is the owner of the team
    if request.user.profile == team.owner:
        messages.error(request, _("As the owner, you can't leave the team."))
        return redirect('team', pk=team.id)

    if request.method == "POST":
        team_member = request.member
        team_member.delete()

        messages.success(request, _("You have successfully left the team."))
        return redirect('teams')

    return render(request, 'teams/leave_team.html', {'teamObj': team})
        
    





    
