from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from django.utils import translation
from users.models import User, COACH, ATHLETE
from .models import Profile
from PIL import Image
from io import BytesIO
from teams.models import Invitation, TeamMember, AthleteInvitation
from .forms import CustomUserCreationForm, ProfileForm, CustomCoachCreationForm
from organizations.models import OrganizationInvite, OrganizationMember, OrganizationSizeLimitError, InvalidUserTypeForOrganizationMemberError
from teams.utils import custom_token_error
# Create your views here.

def landing(request):
    if request.user.is_authenticated:
        return redirect('teams')
    
    return render(request, 'users/landing.html')

# def loginUser(request):

#     page = 'login'

#     if request.user.is_authenticated:
#         return redirect('teams')

#     if request.method == 'POST':
#         # username = request.POST['username']
#         username = request.POST['username'].lower()
#         password = request.POST['password']
#         try:
#             user = User.objects.get(username=username)
#         except: 
#             messages.error(request,_('Username or password is incorrect'))

#         user = authenticate(request, username=username, password=password)

#         if user is not None:
#             login(request, user)
#             return redirect('teams')

#         else:
#             messages.error(request,_('Username or password is incorrect'))

#     context = {'page': page}
#     return render(request, 'users/login_register.html', context)

def loginUser(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('teams')

    if request.method == 'POST':
        username = request.POST['username'].lower()
        password = request.POST['password']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is not None:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('teams')
        
        # If username or password is incorrect, show a generic error message
        messages.error(request, _('Username or password is incorrect'))

    context = {'page': page}
    return render(request, 'users/login_register.html', context)

def logoutUser(request):
    logout(request)
    messages.success(request,_('User was logged out'))
    return redirect('login')



# def registerUser(request):
#     page = 'register'
#     form = CustomUserCreationForm()
    
#     if request.user.is_authenticated:
#         return redirect('teams')

#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.username = user.username.lower().strip()
#             user.email = user.email.lower().strip()
#             email_verification = User.objects.filter(email=user.email)
#             username = user.username
#             username_verification = User.objects.filter(username=username)

#             if len(email_verification) == 0 and len(username_verification) == 0:
#                 user.save()
#                 messages.success(request, 'User account was created')
#                 login(request, user)
#                 return redirect('edit-account')
#             else:
#                 if len(username_verification) > 0:
#                     messages.error(request, 'Username already taken')
#                 if len(email_verification) > 0:
#                     messages.error(request, 'E-mail already used')
#         else:
#             # Handle form errors
#             form_errors = form.errors
#             for field, errors in form_errors.items():
#                 for error in errors:
#                     messages.error(request, f"{field}: {error}")

#     context = {'page': page, 'form': form}
#     return render(request, 'users/login_register.html', context)

def registerAthlete(request, token):
    page = 'register'
    
    if request.user.is_authenticated:
        return redirect('teams')
    
    try:
        # Look up the OrganizationInvite object using the provided token
        invite = AthleteInvitation.objects.get(token=token)

        if invite.is_expired():
            # Token has expired, handle this case
            return custom_token_error(request, _('This invitation link has expired.')) 
        if invite.accepted == True:
            # Token have already accepted, handle this case
            return custom_token_error(request, _('This invitation has already used.')) 
         
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            form.email = invite.email 
            
            if form.is_valid():
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.username = user.username.lower().strip()
                    user.email = invite.email
                    user.user_type = ATHLETE
                    user.save()
                    # Log in the newly created user
                    user = authenticate(request, username=user.username, password=form.cleaned_data['password1'])
                    login(request, user)
                    # Mark the invite as accepted
                    invite.accepted = True
                    invite.save()
                    # Add the registered coach to org members
                    userProfile = Profile.objects.get(user=user)
                    TeamMember.objects.create(profileID=userProfile, teamID=invite.team)
                    messages.success(request, _('Athlete account was created successfully'))
                    return redirect('edit-account')
            else:
                # Handle form errors
                form_errors = form.errors
                for field, errors in form_errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = CustomUserCreationForm()

    except AthleteInvitation.DoesNotExist:
        # Handle the case where the token is not found
        return custom_token_error(request, _('Invalid registration link.')) 

    context = {'page': page, 'form': form, 'token':token}
    return render(request, 'users/login_register.html', context)
    


def registerCoach(request, token):
    page = 'register-coach'
    if request.user.is_authenticated:
        return redirect('teams')

    try:
        # Look up the OrganizationInvite object using the provided token
        invite = OrganizationInvite.objects.get(token=token)

        if invite.is_expired():
            # Token has expired, handle this case
            return custom_token_error(request, _('This invitation link has expired.')) 
        if invite.accepted == True:
            # Token have already accepted, handle this case
            return custom_token_error(request, _('This invitation has already used.')) 
        
        if invite.already_user == True:
            # Token have already accepted, handle this case
            return custom_token_error(request, _('Invalid link.')) 
        
        
        if request.method == 'POST':
            form = CustomCoachCreationForm(request.POST)
            form.email = invite.email 
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        user = form.save(commit=False)
                        user.username = user.username.lower().strip()
                        user.email = invite.email
                        user.user_type = COACH
                        user.save()
                        # Mark the invite as accepted
                        invite.accepted = True
                        invite.save()
                        # Add the registered coach to org members
                        userProfile = Profile.objects.get(user=user)
                        OrganizationMember.objects.create(profile=userProfile, organization=invite.organization)
                        # Log in the newly created user
                        user = authenticate(request, username=user.username, password=form.cleaned_data['password1'])
                        login(request, user)
                        messages.success(request, _('Coach account was created successfully'))
                        return redirect('edit-account')
                except (InvalidUserTypeForOrganizationMemberError, OrganizationSizeLimitError) as e:
                    messages.error(request, str(e))
                
            else:
                # Handle form errors
                form_errors = form.errors
                for field, errors in form_errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = CustomCoachCreationForm()

    except OrganizationInvite.DoesNotExist:
        # Handle the case where the token is not found
        return custom_token_error(request, _('Invalid registration link.')) 

    except OrganizationInvite.DoesNotExist:
        # Handle the case where the token is not found
        return custom_token_error(request, _('Invalid registration link.')) 

    context = {'page': page, 'form': form, 'token':token}
    return render(request, 'users/register_coach.html', context)
    

# @login_required(login_url="login")
# def accept_invitation(request, token):
#     try:
#         invitation = Invitation.objects.get(token=token)
#     except Invitation.DoesNotExist:
#         messages.error(request, _('Invalid invitation link'))
#         return redirect('teams')
    

#     if invitation.accepted:
#         messages.warning(request, _('Invitation already accepted'))
#         return redirect('teams')

#     if invitation.is_expired():
#         messages.error(request, _('Invitation has expired'))
#         return redirect('teams')

#     if invitation.email != request.user.email:
#         messages.error(request, 'Not allowed')
#         return redirect('teams')

#     if request.method == 'POST':
#         profile = request.user.profile
#         if profile.email == invitation.email:
#             if TeamMember.objects.filter(profileID=profile, teamID=invitation.team, is_active=True).exists():
#                 messages.warning(request, _('You are already a member of this team'))
#                 return redirect('teams')
#             team_member = TeamMember(profileID=profile, teamID=invitation.team, role=invitation.role)
#             team_member.save()

#             invitation.accepted = True
#             invitation.save()

#             messages.success(request, _('You have joined the team'))
#             return redirect('teams')
#         messages.error(request, _('Error occoured'))
#         return redirect('teams')
#     context =  {'invitation': invitation}
#     return render(request, 'users/accept_invite.html', context)

@login_required(login_url="login")
def accept_invitation(request, token):
    try:
        invitation = Invitation.objects.get(token=token)
    except Invitation.DoesNotExist:
        messages.error(request, _('Invalid invitation link'))
        return redirect('teams')

    if invitation.accepted:
        messages.warning(request, _('Invitation already accepted'))
        return redirect('teams')

    if invitation.is_expired():
        messages.error(request, _('Invitation has expired'))
        return redirect('teams')

    if invitation.email != request.user.email:
        messages.error(request, _('Not allowed'))
        return redirect('teams')

    if request.method == 'POST':
        profile = request.user.profile
        if profile.email == invitation.email:
            team_member, created = TeamMember.objects.get_or_create(profileID=profile, teamID=invitation.team)

            # If the team member exists but is inactive, set it to active
            if not created and not team_member.is_active:
                team_member.is_active = True
                team_member.role = invitation.role
                team_member.save()
                messages.success(request, _('You have re-joined the team'))
            else:
                # If the team member doesn't exist or is active, create a new one
                if not TeamMember.objects.filter(profileID=profile, teamID=invitation.team, is_active=True).exists():
                    team_member = TeamMember(profileID=profile, teamID=invitation.team, role=invitation.role)
                    team_member.save()
                    messages.success(request, _('You have joined the team'))
                else:
                    messages.warning(request, _('You are already a member of this team'))
                    return redirect('teams')

            invitation.accepted = True
            invitation.save()

            return redirect('teams')
        messages.error(request, _('Error occurred'))
        return redirect('teams')

    context = {'invitation': invitation}
    return render(request, 'users/accept_invite.html', context)


@login_required(login_url="login")
def acceptOrgInvitation(request, token):
    try:
        invitation = OrganizationInvite.objects.get(token=token)
    except OrganizationInvite.DoesNotExist:
        return custom_token_error(request, _('Invalid invitation link'))
    
    if invitation.accepted:
        return custom_token_error(request, _('Invitation already accepted'))

    if invitation.is_expired():
        return custom_token_error(request, _('Invitation has expired'))
    
    if invitation.already_user == False:
        messages.error(request, _('Invalid invitation link'))

    if invitation.email != request.user.email:
        return custom_token_error(request, _('Not allowed'))
    
    if request.method == 'POST':
        profile = request.user.profile
        if profile.email == invitation.email:
            if OrganizationMember.objects.filter(profile=profile, organization=invitation.organization).exists():
                messages.warning(request, _('You are already a member of this organization'))
                return redirect('organizations')
            org_member = OrganizationMember(profile=profile, organization=invitation.organization)
            org_member.save()

            invitation.accepted = True
            invitation.save()

            messages.success(request, _('You have joined to new sport organization'))
            return redirect('organizations')
        messages.error(request, _('Error occoured'))
        return redirect('organizations')
    context =  {'invitation': invitation}
    return render(request, 'users/accept_org_invite.html', context)



@login_required(login_url="login")
def userAccount(request):
    profile = request.user.profile
    context = {'profile': profile}
    return render(request, 'users/account.html', context)


# @login_required(login_url="login")
# def editAccount(request):
#     profile = request.user.profile
#     form = ProfileForm(instance=profile)

#     if request.method == 'POST':
#         form = ProfileForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, _('Account updated'))
#             return redirect('edit-account')
#     domain = 'https://'+ settings.AWS_S3_CUSTOM_DOMAIN
#     context = {'form': form, 'domain': domain,}
#     return render(request, 'users/edit-account.html', context)

@login_required(login_url="login")
def editAccount(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)
    oldimage = profile.profile_image
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile_image = form.cleaned_data['profile_image']

            # Resize image only if a new image is uploaded
            if profile_image and profile_image != oldimage:
                # Read the image data from the uploaded file
                img_data = profile_image.read()
                # Open the image using Pillow
                img = Image.open(BytesIO(img_data))

                # Get the original width and height
                width, height = img.size

                # Calculate the new maximum dimension to maintain aspect ratio
                max_size = 300
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
                profile_image.seek(0)
                profile_image.write(resized_img_data.getvalue())

            form.save()
            messages.success(request, _('Account updated'))
            return redirect('edit-account')
    domain = 'https://'+ settings.AWS_S3_CUSTOM_DOMAIN
    context = {'form': form, 'domain': domain,}
    return render(request, 'users/edit-account.html', context)

@login_required(login_url="login")
def deleteUserAccount(request):
    # vajag uztaisit, kad pieprasa ievadit password
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, _('Sad to see you leaving us! User was deleted successfully'))
        return redirect('home')

    context = {}
    return render(request, 'users/delete_account.html', context)

