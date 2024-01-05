from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.conf import settings
from django.core.mail import send_mail
from django.forms import modelformset_factory
from django.utils.translation import gettext as _
from .models import OrganizationInvite, Organizations ,OrganizationMember, OrganizationPhysicalAssessment, CoachManager, Manager, Coach
from .forms import InviteToOrgForm, OrgMemberForm, OrgPhysicalAssessmentForm
from .utils import paginateAthletes, paginateTeams, searchAthlete, searchTeams
from users.models import Profile, ATHLETE
from teams.models import Team, TeamMember
from teams.utils import custom_forbidden, custom_token_error, custom_team_limit_msg
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
    teams_owned_by_requser = Team.objects.filter(owner=requser, organization=org)


    context = {'org': org, 'org_members': org_members_with_names, 'subscription_plan': subscription_plan, 'requser':requser, 'total_teams': total_teams, 'teams_owned_by_requser': teams_owned_by_requser}
    return render(request, 'organizations/organization-single.html', context)

@login_required(login_url="login")
@user_is_org_owner
def invite_to_organization(request, pk):
    org = request.org
    owner = request.owner
    requser = request.org_member
    form = InviteToOrgForm()
    org_members = org.organizationmember_set.select_related('profile')
    subscription_plan = org.subscription_plan

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

    return render(request, 'organizations/invite.html', {'form': form, 'org': org, 'subscription_plan': subscription_plan, 'org_members': org_members, 'requser': requser})

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
    subscription_plan = org.subscription_plan

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
        'subscription_plan': subscription_plan
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
    athlete = get_object_or_404(TeamMember, pk=aid)

    # Check if the user has the right role or is the owner of the organization or the team
    is_authorized = organization_member.org_role in [CoachManager, Manager] or \
                    org.owner == request.user.profile or \
                    athlete.teamID.owner == organization_member

    if not is_authorized:
        messages.error(request, "You don't have permission to view this athlete.")
        return redirect('browse-org-athletes', pk=org.id)  

    context = {
        'requser': organization_member,
        'org': org,
        'athlete': athlete,
    }

    return render(request, 'organizations/browse_single_athlete.html', context)



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
        messages.error(request, "You don't have permission to view this team.")
        return redirect('browse-org-teams', pk=org.id)  

    context = {
        'requser': organization_member,
        'org': org,
        'team': team,
        
    }

    return render(request, 'organizations/browse_single_team.html', context)

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
        organization=org.id
    )

    if request.method == 'POST':
        form = OrgPhysicalAssessmentForm(request.POST, instance=physical_assessment)
        if form.is_valid():
            record = form.save(commit=False)
            record.organization = org
            record.save()
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
        organization=org.id
    )

    if request.method == 'POST':
        physical_assessment.delete()
        return redirect('all-org-pa', pk=pk)
    
    context = {'org': org, 'object': physical_assessment, 'requser': organization_member}
    return render(request, 'organizations/delete_org_physical_assessment.html', context)