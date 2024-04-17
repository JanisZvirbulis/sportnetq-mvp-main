import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.conf import settings
from django.core.mail import send_mail
from django.forms import modelformset_factory
from datetime import timedelta, datetime, date, time
import calendar
from calendar import monthrange
from django.utils import timezone
from django.utils.translation import gettext as _
from .models import OrganizationInvite, Organizations ,OrganizationMember, OrganizationPhysicalAssessment, CoachManager, Manager, Coach
from .forms import InviteToOrgForm, OrgMemberForm, OrgPhysicalAssessmentForm, OrgTeamSeasonForm, orgAthleteTeamSelectForm, orgAthletePATeamSelectForm, orgAthleteAnalyticsTeamSelectForm
from .utils import paginateAthletes, paginateTeams, searchAthlete, searchTeams, AthleteCalendar
from users.models import Profile, ATHLETE
from teams.models import Team, TeamMember, AttendanceRecord, Event, TeamSeason, OrganizationPhysicalAssessmentScore
from teams.utils import custom_forbidden, custom_token_error, custom_team_limit_msg, Calendar, generate_event_data, generate_attendance_data, generate_org_team_members_data, generate_happened_event_data, generate_happened_athlete_event_data, generate_athlete_evemt_data
from teams.forms import TeamForm

OWNER_ROLE = '4'

def user_is_org_member(view_func):
    def _wrapped_view(request, *args, **kwargs):

        if request.user.user_type == ATHLETE:
            return redirect('teams')
        
        org = get_object_or_404(Organizations, pk=kwargs['pk'])

        try:
            org_member = OrganizationMember.objects.select_related('profile').get(profile=request.user.profile, organization=org)
        except OrganizationMember.DoesNotExist:
            return custom_forbidden(request, _("You are not a member of this organization."))
        org_members = org.organizationmember_set.select_related('profile')

        request.org = org
        request.org_member = org_member
        request.org_members = org_members
        if org_member:
            return view_func(request, *args, **kwargs)
        else:
            return custom_forbidden(request, _("Not allowed! You must be a member of this organization to access this page."))
    return _wrapped_view

def user_is_org_owner(view_func):
    def _wrapped_view(request, *args, **kwargs):

        if request.user.user_type == ATHLETE:
            return redirect('teams')
        
        org = get_object_or_404(Organizations, pk=kwargs['pk'])
        
        try:
            member = OrganizationMember.objects.select_related('profile', 'organization').get(profile=request.user.profile, organization=org)
        except OrganizationMember.DoesNotExist:
            return custom_forbidden(request, _("You are not a member of this organization."))
        
        if member.profile != org.owner:
            return custom_forbidden(request, _("You are not a owner of this organization."))
        
        request.org = org
        request.owner = org.owner
        request.org_member = member
        return view_func(request, *args, **kwargs)

    return _wrapped_view



def get_teams_for_athlete(org, organization_member, athleteProfile, request):
    if organization_member.org_role in [CoachManager, Manager] or org.owner == request.user.profile:
        teams_for_profile_base = TeamMember.objects.filter(
            profileID=athleteProfile,
            teamID__organization=org
        ).order_by('teamID__teamName')
    elif organization_member.org_role == Coach:
        teams_for_profile_base = TeamMember.objects.filter(
            profileID=athleteProfile,
            teamID__organization=org,
            teamID__owner=organization_member
        ).order_by('teamID__teamName')
    else:
        teams_for_profile_base = TeamMember.objects.none()

    return teams_for_profile_base


# VIEW FUNCTIONS

@login_required(login_url="login")
def organizations(request):
    if request.user.user_type == ATHLETE:
        return custom_forbidden(request, _("You must have coach account to access organization page"))

    requserid = request.user.profile.id
    orgs = OrganizationMember.objects.select_related('organization').filter(profile=requserid)
    context = {'orgs': orgs}

    return render(request, 'organizations/organizations.html', context)

@login_required(login_url="login")
@user_is_org_member
def singleOrganization(request, pk):
    # Access the associated organization from the OrganizationMember object
    org = request.org
    requser = request.org_member
    # Prefetch all organization members with their names
    org_members_with_names = request.org_members

    subscription_plan = org.subscription_plan
    # Count the number of teams that belong to the current organization
    total_teams = Team.objects.filter(organization=org).aggregate(total_teams=Count('id'))['total_teams']
    # Teams owned by requser
    teams_owned_by_requser = Team.objects.filter(owner=requser, organization=org)
    # All Athletes for requser
    total_athletes_for_requser = TeamMember.objects.filter(teamID__in=teams_owned_by_requser,role=ATHLETE).values('profileID').distinct().count()
    # Count the number of teamMembers athletes that belong to the current organization
    total_athletes = TeamMember.objects.filter(teamID__organization_id=org, role=ATHLETE).values('profileID').distinct().count()


    context = {
        'org': org,
        'org_members': org_members_with_names,
        'subscription_plan': subscription_plan,
        'requser':requser,
        'total_teams': total_teams,
        'teams_owned_by_requser': teams_owned_by_requser,
        'total_athletes': total_athletes,
        'total_athletes_for_requser': total_athletes_for_requser,
        }
    return render(request, 'organizations/organization-single.html', context)

@login_required(login_url="login")
@user_is_org_owner
def invite_to_organization(request, pk):
    org = request.org
    owner = request.owner
    requser = request.org_member
    form = InviteToOrgForm()
    org_members = org.organizationmember_set.select_related('profile')

    if request.method == 'POST':
        form = InviteToOrgForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()

            if Profile.objects.filter(email=email).exists():
                existing_user = Profile.objects.get(email=email)
                is_member = org_members.filter(profile=existing_user).exists()
                if is_member:
                    messages.error(request,_('User with this %(email)s is already a member of this organization.') % {'email': email})
                    return render(request, 'organizations/invite.html', {'form': form, 'org': org, 'org_members': org_members})  
                else: 
                    if existing_user.user.user_type == ATHLETE:
                        messages.error(request, _("You can't invite a user to the organization who is athlete."))
                        return render(request, 'organizations/invite.html', {'form': form, 'org': org, 'org_members': org_members})
                    else:  
                        # If user exist and have coach account and not a member of org, then save invite and send invite email.
                        invite = OrganizationInvite(email=email, organization=org,invited=request.user.profile, already_user=True)
                        invite.save()

                        # TODO: Send email with the invite link (consider using Django's EmailMessage class)
                        accept_invite_url = reverse("accept-org-invitation", args=[invite.token])
                        subject = f' You have been invited to join "{invite.organization.name}" organization'
                        message = f' Please click the link to accept the invitation from organization {invite.organization.name}: {request.build_absolute_uri(accept_invite_url)}'
                        from_email = settings.EMAIL_HOST_USER
                        recipient_list = [email]

                        send_mail(subject, message, from_email, recipient_list, fail_silently=False,)
                        messages.success(request, _('An invitation has been sent to %(email)s.') % {'email': email})
                        return redirect('org-invite', pk=org.id)

            else:
                #  Save Invitation and Send registration email
                invite = OrganizationInvite(email=email, organization=org,invited=request.user.profile, already_user=False)
                invite.save()

                # TODO: Send email with registration link (consider using Django's EmailMessage class)
                accept_invite_url = reverse("register-coach", args=[invite.token])
                subject = f' You have been invited to Sign Up at SportNetQ and join {invite.organization.name} organization'
                message = f' Please click the link to Sign Up at SportNetQ as Coach and join organization {invite.organization.name}: {request.build_absolute_uri(accept_invite_url)}'
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [email]

                send_mail(subject, message, from_email, recipient_list, fail_silently=False,)
                
                messages.success(request, _('Invitation to Coach registration has been sent to %(email)s.') % {'email': email})
                return redirect('org-invite', pk=org.id)
        else:
             # Form is not valid
            messages.error(request, _('Invalid form submission. Please check your input.'))

    return render(request, 'organizations/invite.html', {'form': form, 'org': org, 'org_members': org_members, 'requser': requser})

@login_required(login_url="login")
@user_is_org_member
def orgMembers(request, pk):
    org = request.org
    requser = request.org_member
    subscription_plan = org.subscription_plan
    org_members_with_names = request.org_members.order_by('profile__name')

    context = {'org': org, 'org_members': org_members_with_names, 'subscription_plan': subscription_plan, 'requser':requser}
    return render(request, 'organizations/org-members.html', context)


@login_required(login_url="login")
@user_is_org_owner
def editOrgMembers(request, pk):
    org = request.org
    owner = request.owner
    requser = request.org_member
    org_members = org.organizationmember_set.exclude(org_role='4').select_related('profile').order_by('profile__name')
    memberListFormSet =  modelformset_factory(OrganizationMember, form=OrgMemberForm, extra=0)
    formset = memberListFormSet(queryset=org_members)

    if request.method == 'POST':
        formset = memberListFormSet(request.POST, queryset=org_members)
        if formset.is_valid():
            formset.save()
            return redirect('org-members', pk=org.id)
        else:
            messages.error(request, _('An error has occurred editing members'))
    
    return render(request, 'organizations/org-members-edit.html', {
        'org': org,
        'owner': owner,
        'org_members': org_members,
        'formset': formset,
        'role': request.user.user_type,
        'requser': requser,
    })

@login_required(login_url="login")
@user_is_org_member
def createTeamForOrg(request, pk):

    if request.user.user_type == ATHLETE:
        return redirect('teams')
    
    org = request.org
    organization_member = request.org_member
    subscription_plan = org.subscription_plan
    
    teams = Team.objects.filter(owner=organization_member)  
    form = TeamForm()
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if len(teams) < subscription_plan.team_limit_for_coach:
            if form.is_valid():
                team = form.save(commit=False)
                team.owner = organization_member
                team.organization = organization_member.organization
                team.save()
                TeamMember.objects.create(
                    teamID=team,
                    profileID=request.user.profile,
                    role=OWNER_ROLE,
                )
                return redirect('teams')
        else:
            messages.error(request, custom_team_limit_msg(subscription_plan.team_limit_for_coach))
            # messages.error(request, 'max team count reached, for your subscription plan')

    context = {'form': form, 'org': org}
    return render(request, 'organizations/team_form.html', context)


@login_required(login_url="login")
@user_is_org_member
def browseOrgAthletes(request, pk):
    org = request.org
    organization_member = request.org_member


       # Use the constants directly for role checking
    if organization_member.org_role in [CoachManager, Manager] or org.owner == request.user.profile:
        # Fetch all teams that belong to the organization for Manager, CoachManager or Owner
        teams_in_org = Team.objects.filter(organization=org).order_by('teamName')
    elif organization_member.org_role == Coach:
        # Fetch only the teams coached by this user
        teams_in_org = Team.objects.filter(organization=org, owner=organization_member).order_by('teamName')
    else:
        # Handle other cases or deny access
        teams_in_org = Team.objects.none()

    athletes, search_query = searchAthlete(request, teams_in_org)

    # Pagination
    custom_range, athletes_paged = paginateAthletes(request, athletes, results=16) 

    context = {
        'requser': organization_member,
        'org': org,
        'athletes': athletes_paged,
        'teams_in_org': teams_in_org,
        'custom_range': custom_range,
        'search_query': search_query,
    }

    return render(request, 'organizations/browse_athletes.html', context)

@login_required(login_url="login")
@user_is_org_member
def browseOrgSingleAthlete(request, pk, aid):
    org = request.org
    organization_member = request.org_member

    # Retrieve the athlete
    athleteProfile = get_object_or_404(Profile, pk=aid)

    if organization_member.org_role in [CoachManager, Manager] or org.owner == request.user.profile:
        teams_for_profile_base = TeamMember.objects.filter(
        profileID=athleteProfile,
        teamID__organization=org
        ).order_by('teamID__teamName')
    elif organization_member.org_role == Coach:
        teams_for_profile_base = TeamMember.objects.filter(
        profileID=athleteProfile,
        teamID__organization=org,
        teamID__owner=organization_member
        ).order_by('teamID__teamName')
    else:
        teams_for_profile_base = TeamMember.objects.none()

    team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)

    current_date = timezone.now().date()
    member_calendar = AttendanceRecord.objects.filter(
        team_member__profileID=athleteProfile,
        team__id__in=team_ids,
        event__start_time__date__gte=current_date
    ).prefetch_related('event').order_by('event__start_time')[:5]

    context = {
        'requser': organization_member,
        'teams_for_athlete': teams_for_profile_base,
        'org': org,
        'athlete': athleteProfile,
        'member_calendar': member_calendar,
    }

    return render(request, 'organizations/browse_single_athlete.html', context)

@login_required(login_url="login")
@user_is_org_member
def OrgAthleteCalendar(request, pk, aid):
    org = request.org
    organization_member = request.org_member
    athleteProfile = get_object_or_404(Profile, pk=aid)

    teams_for_profile_base = get_teams_for_athlete(org, organization_member, athleteProfile, request)
    d = get_date(request.GET.get('month', None))
    if request.method == 'POST':
        form = orgAthleteTeamSelectForm(request.POST, teams=teams_for_profile_base)
        if form.is_valid():
            selected_team_id = form.cleaned_data['team']
            if selected_team_id:
                 team_ids = [selected_team_id]
            else:
                team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)
            cal = AthleteCalendar(d.year, d.month, athleteProfile, team_ids, org)
    else:
        form = orgAthleteTeamSelectForm(teams=teams_for_profile_base)
        team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)
        cal = AthleteCalendar(d.year, d.month, athleteProfile, team_ids, org)
                 
    html_cal = cal.formatmonth(withyear=True)
    calendar =  html_cal
    prevm = prev_month(d)
    nextm = next_month(d)
    context = {
        'requser': organization_member,
        'teams_for_athlete': teams_for_profile_base,
        'org': org,
        'athlete': athleteProfile,
        'calendar': calendar, 
        'prev_month': prevm, 
        'next_month': nextm,
        'form': form
    }
    return render(request, 'organizations/orgAthleteCalendar.html', context)

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


@login_required(login_url="login")
@user_is_org_member
def OrgAthletePhysicalAssessment(request, pk, aid):
    org = request.org
    organization_member = request.org_member
    athleteProfile = get_object_or_404(Profile, pk=aid)

    teams_for_profile_base = get_teams_for_athlete(org, organization_member, athleteProfile, request)
    if request.method == 'POST':
        form = orgAthletePATeamSelectForm(request.POST, teams=teams_for_profile_base)
        if form.is_valid():
            selected_team_id = form.cleaned_data['team']
            if selected_team_id:
                team_ids = [selected_team_id]
            else:
                team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)
            orgPA_scores = OrganizationPhysicalAssessmentScore.objects.filter(
                team__id__in=team_ids,
                team_member__profileID=athleteProfile,
                organization=org
            ).select_related('org_physical_assessment', 'org_physical_assessment_record', 'team_member', 'team', 'organization').order_by('org_physical_assessment__opa_title','-org_physical_assessment_record__org_physical_assessment_date')

    else:
        form = orgAthletePATeamSelectForm(teams=teams_for_profile_base)
        team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)
        orgPA_scores = OrganizationPhysicalAssessmentScore.objects.filter(
            team__id__in=team_ids,
            team_member__profileID=athleteProfile,
            organization=org
        ).select_related('org_physical_assessment', 'org_physical_assessment_record', 'team_member', 'team', 'organization').order_by('org_physical_assessment__opa_title','-org_physical_assessment_record__org_physical_assessment_date')
 
    context = {
        'requser': organization_member,
        'teams_for_athlete': teams_for_profile_base,
        'org': org,
        'athlete': athleteProfile,
        'form': form,
        'orgPA_scores': orgPA_scores,
    }
    return render(request, 'organizations/orgAthletePhysicalAssessments.html', context)

@login_required(login_url="login")
@user_is_org_member
def OrgAthleteAnalytics(request, pk, aid):
    org = request.org
    organization_member = request.org_member
    athleteProfile = get_object_or_404(Profile, pk=aid)

    teams_for_profile_base = get_teams_for_athlete(org, organization_member, athleteProfile, request)
    current_timezone = timezone.get_current_timezone()
    form_initial_data = {}
    form = orgAthleteAnalyticsTeamSelectForm(request.POST or None, teams=teams_for_profile_base, initial=form_initial_data) 
    if request.method == 'POST' and form.is_valid():
        if form.is_date_valid('start_date') and form.is_date_valid('end_date'):
            selected_team_id = form.cleaned_data['team']
            start_date = timezone.make_aware(timezone.datetime.combine(form.cleaned_data.get('start_date') , time.min), timezone=current_timezone)
            end_date = timezone.make_aware(timezone.datetime.combine(form.cleaned_data.get('end_date') , time.max), timezone=current_timezone)
            if selected_team_id:
                team_ids = [selected_team_id]
            else:
                team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)
                
            team_member_attendance = AttendanceRecord.objects.filter(
                team_member__profileID=athleteProfile,
                team__id__in=team_ids,
                event__start_time__gte=start_date,
                event__start_time__lte=end_date,
            ).select_related('event').order_by('event__start_time')
        else:
            messages.error(request, _("Please enter valid start and end date."))
            return redirect('org-athlete-analytics', pk=org.id, aid=athleteProfile.id) 
    else:
        initial_start_date = timezone.make_aware(timezone.datetime.combine(timezone.now().replace(day=1).date() , time.min), timezone=current_timezone)
        last_day = calendar.monthrange(timezone.now().year, timezone.now().month)[1]
        initial_end_date = timezone.make_aware(timezone.datetime.combine(timezone.now().replace(day=last_day).date() , time.min), timezone=current_timezone)
        team_ids = teams_for_profile_base.values_list("teamID__id", flat=True)
        team_member_attendance = AttendanceRecord.objects.filter(
            team_member__profileID=athleteProfile,
            team__id__in=team_ids, 
            event__start_time__gte=initial_start_date,
            event__start_time__lte=initial_end_date,
        ).select_related('event').order_by('event__start_time')
        
    team_member_attendance_with_value = team_member_attendance.exclude(
        attendance=AttendanceRecord.EMPTYVALUE
    )

    member_attendance_data = generate_attendance_data(team_member_attendance_with_value)
    happened_event_data = generate_happened_athlete_event_data(team_member_attendance, team_member_attendance_with_value)
    event_data = generate_athlete_evemt_data(team_member_attendance)
  
    context = {
        'requser': organization_member,
        'teams_for_athlete': teams_for_profile_base,
        'org': org,
        'athlete': athleteProfile,
        'form': form,
        'attendance_data':team_member_attendance,
        'member_attendance_data': member_attendance_data,
        'happened_event_data': happened_event_data,
        'event_data': event_data,
    }
    return render(request, 'organizations/orgAthleteAnalytics.html', context)

@login_required(login_url="login")
@user_is_org_member
def browseOrgTeams(request, pk):
    org = request.org
    organization_member = request.org_member

    # Determine which teams to include based on the user's role
    if organization_member.org_role in [CoachManager, Manager] or org.owner == request.user.profile:
        teams_in_org = Team.objects.filter(organization=org).order_by('teamName')
    elif organization_member.org_role == Coach:
        teams_in_org = Team.objects.filter(organization=org, owner=organization_member).order_by('teamName')
    else:
        teams_in_org = Team.objects.none()

    # Search teams if search_query is provided
    teams_in_org, search_query = searchTeams(request, teams_in_org)

    # Pagination
    custom_range, teams_paged = paginateTeams(request, teams_in_org, results=12)

    context = {
        'requser': organization_member,
        'org': org,
        'teams_in_org': teams_paged,
        'custom_range': custom_range,
        'search_query': search_query
    }

    return render(request, 'organizations/browse_teams.html', context)


@login_required(login_url="login")
@user_is_org_member
def browseOrgSingleTeam(request, pk, tid):
    org = request.org
    organization_member = request.org_member
    team = get_object_or_404(Team, pk=tid)

    is_authorized = organization_member.org_role in [CoachManager, Manager] or \
                    org.owner == request.user.profile or \
                    team.owner == organization_member

    if not is_authorized:
        messages.error(request, _("You don't have permission to view this team."))
        return redirect('browse-org-teams', pk=org.id)  

    team_members = TeamMember.objects.select_related('profileID').filter(teamID=team)
    team_members_sorted = team_members.order_by('role', 'profileID__name')
    owner_with_profile = OrganizationMember.objects.select_related('profile').get(id=team.owner.id)
    context = {
        'requser': organization_member,
        'org': org,
        'team': team,
        'team_members': team_members_sorted,
        'owner': owner_with_profile,
    }

    return render(request, 'organizations/browse_single_team.html', context)

@login_required(login_url="login")
@user_is_org_member
def browseOrgSingleTeamCalendar(request, pk, tid):
    org = request.org
    organization_member = request.org_member
    team = get_object_or_404(Team, pk=tid)

    is_authorized = organization_member.org_role in [CoachManager, Manager] or \
                    org.owner == request.user.profile or \
                    team.owner == organization_member

    if not is_authorized:
        messages.error(request, _("You don't have permission to view this team."))
        return redirect('browse-org-teams', pk=org.id)  

    d = get_org_date(request.GET.get('month', None))
    cal = Calendar(d.year, d.month, tid, team, True)          
    html_cal = cal.formatmonth(withyear=True)
    calendar =  html_cal
    prevm = prev_month_org_team(d)
    nextm = next_month_org_team(d)
    context = {'org': org, 'requser': organization_member, 'team': team, 'calendar': calendar, 'prev_month': prevm, 'next_month': nextm}

    return render(request, 'organizations/org-team-calendar.html', context)

def get_org_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month_org_team(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month_org_team(d):
    days_in_month = monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

@login_required(login_url="login")
@user_is_org_member
def orgSingleTeamAnalytics(request, pk, tid):
    org = request.org
    organization_member = request.org_member
    team = get_object_or_404(Team, pk=tid)
    is_authorized = organization_member.org_role in [CoachManager, Manager] or \
                    org.owner == request.user.profile or \
                    team.owner == organization_member

    if not is_authorized:
        messages.error(request, _("You don't have permission to view this team."))
        return redirect('browse-org-teams', pk=org.id) 
    
    current_season = TeamSeason.objects.filter(team=team, current_season=True).first()
    form_initial_data = {}
    current_timezone = timezone.get_current_timezone()
    if current_season:
        form_initial_data['start_date'] = timezone.make_aware(timezone.datetime.combine(current_season.start_date, time.min), timezone=current_timezone)
        form_initial_data['end_date'] = timezone.make_aware(timezone.datetime.combine(current_season.end_date, time.max), timezone=current_timezone)
   
    form = OrgTeamSeasonForm(request.POST or None, team=team, initial=form_initial_data) 
    
    if request.method == 'POST' and form.is_valid():
        if form.is_date_valid('start_date') and form.is_date_valid('end_date'):
            start_date = timezone.make_aware(timezone.datetime.combine(form.cleaned_data.get('start_date') , time.min), timezone=current_timezone)
            end_date = timezone.make_aware(timezone.datetime.combine(form.cleaned_data.get('end_date') , time.max), timezone=current_timezone)
            team_attendance = team.attendancerecord_set.filter(
                team=team.id,
                event__start_time__range=(start_date, end_date)
            )
            team_events = team.events.filter(
                teamID=team.id,
                start_time__range=(start_date, end_date)
            )
    # Both start_date and end_date are valid dates
        else:
            messages.error(request, _("Please enter valid start and end date."))
            return redirect('org-single-team-analytics', pk=org.id, tid=team.id) 
    else:
        start_date = form_initial_data.get('start_date') or timezone.make_aware(timezone.datetime.combine(timezone.now() - timedelta(days=365), time.min), timezone=current_timezone) # Default to one year ago
        end_date = form_initial_data.get('end_date') or timezone.make_aware(timezone.datetime.combine(timezone.now(), time.max), timezone=current_timezone)
        team_attendance = team.attendancerecord_set.filter(
            team=team.id,
            event__start_time__range=(start_date, end_date)
        )
        team_events = team.events.filter(
            teamID=team.id,
            start_time__range=(start_date, end_date)
        )

    attendance_data = generate_attendance_data(team_attendance)
    happened_event_data = generate_happened_event_data(team_events, team_attendance)
    team_members_data = generate_org_team_members_data(team, current_season, start_date, end_date)
    event_data = generate_event_data(team_events)

    context = {
        'team': team,
        'team_events': team_events,
        'requser': organization_member,
        'event_data': event_data,
        'team_attendance': team_attendance,
        'attendance_data': attendance_data,
        'team_members_data': team_members_data,
        'happened_event_data': happened_event_data,
        'form': form,
        'org': org,
    }

    return render(request, 'organizations/org-team-analytics.html', context)

@login_required(login_url="login")
@user_is_org_owner
def orgSettings(request, pk):
    org = request.org
    organization_member = request.org_member
    context = {'org': org, 'requser': organization_member}
    return render(request, 'organizations/org_settings.html', context)
    
@login_required(login_url="login")
@user_is_org_owner
def allOrgPhysicalAssessment(request, pk):
    org = request.org
    organization_member = request.org_member
    physical_assessments = OrganizationPhysicalAssessment.objects.filter(organization=pk)
    context = {'org': org, 'records': physical_assessments, 'requser': organization_member}
    return render(request, 'organizations/org_physical_assessments.html', context)

@login_required(login_url="login")
@user_is_org_owner
def createOrgPhysicalAssessment(request, pk):
    org = request.org
    organization_member = request.org_member

    form = OrgPhysicalAssessmentForm()

    if request.method == 'POST':
        form = OrgPhysicalAssessmentForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.organization = org
            record.save()
            return redirect('all-org-pa', pk=pk)
        else:
            messages.error(request, _('Invalid form submission. Please check your input.'))
    context = {'org': org, 'form': form, 'requser': organization_member}
    return render(request, 'organizations/org_physical_assessments_form.html', context)

@login_required(login_url="login")
@user_is_org_owner
def viewOrgPhysicalAssessment(request, pk, id):
    org = request.org
    organization_member = request.org_member
    physical_assessment = get_object_or_404(
        OrganizationPhysicalAssessment,
        id=id,
        organization=pk
    )
    context = {'org': org, 'record': physical_assessment, 'requser': organization_member}
    return render(request, 'organizations/view_org_physical_assessment.html', context)

@login_required(login_url="login")
@user_is_org_owner
def editOrgPhysicalAssessment(request, pk, id):
    org = request.org
    organization_member = request.org_member
    physical_assessment = get_object_or_404(
        OrganizationPhysicalAssessment,
        id=id,
        organization=pk
    )

    if request.method == 'POST':
        form = OrgPhysicalAssessmentForm(request.POST, instance=physical_assessment)
        if form.is_valid():
            form.save()
            return redirect('all-org-pa', pk=pk)
        else:
            messages.error(request, _('Invalid form submission. Please check your input.'))
    else:
        form = OrgPhysicalAssessmentForm(instance=physical_assessment)

    context = {'org': org, 'record': physical_assessment, 'form': form, 'requser': organization_member}
    return render(request, 'organizations/edit_org_physical_assessment.html', context)


@login_required(login_url="login")
@user_is_org_owner
def deleteOrgPhysicalAssessment(request, pk, id):
    org = request.org
    organization_member = request.org_member
    physical_assessment = get_object_or_404(
        OrganizationPhysicalAssessment,
        id=id,
        organization=pk
    )

    if request.method == 'POST':
        physical_assessment.delete()
        return redirect('all-org-pa', pk=pk)
    
    context = {'org': org, 'object': physical_assessment, 'requser': organization_member}
    return render(request, 'organizations/delete_org_physical_assessment.html', context)