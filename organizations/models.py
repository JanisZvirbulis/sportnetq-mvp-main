from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from users.models import User
from django.db.models import Count
import uuid
from users.models import Profile, COACH, MANAGEMENT
# from teams.models import Team, TeamMember

# Create your models here.
Coach = '1'
CoachManager = '2'
Manager = '3'
Owner = '4'
org_role_choice = (
    (Coach , _('Coach')),
    (CoachManager, _('Coach/Manager')),
    (Manager, _('Manager')),
    (Owner, _('Owner')),
)

class SubscriptionPlan(models.Model):
    code = models.CharField(max_length=2, primary_key=True) # code 1. 2. 3 etc.
    name = models.CharField(max_length=100)
    org_member_limit = models.IntegerField()  # size of member count for each subscription plan
    team_limit_for_coach =  models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)],default=2)
    team_member_limit = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)],default=30)
    tactic_play_limit =  models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)],default=10)
    tactic_count_limit =  models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)],default=5)

    def __str__(self):
        return self.name

class Organizations(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    org_size = models.IntegerField(default=1, editable=False)

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:  # Only perform the check when creating a new Organization
            if self.owner.user.user_type not in [COACH, MANAGEMENT]:
                raise ValidationError(_('Only a Coach or Management can be owner of organization.'))
            
            # ???????? paslaik vajag caur admin paneli izveidot organizaciju un ari izveidot OrgMember ierakstu
            if (OrganizationMember.objects.filter(profile=self.owner).exists() or 
                Organizations.objects.filter(owner=self.owner).exclude(id=self.id).exists()):
                raise ValidationError(_('This profile is already associated with an organization.'))

        if self.subscription_plan:
            self.org_size = self.subscription_plan.org_member_limit
        super().save(*args, **kwargs)

class InvalidUserTypeForOrganizationMemberError(Exception):
    pass

class OrganizationSizeLimitError(Exception):
    pass

class OrganizationMember(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    org_role = models.CharField(
        max_length=2,
        choices=org_role_choice,
        default=org_role_choice[0][0],
        db_index=True,
    )
    def __str__(self):
        return str(self.profile.name + " " + self.organization.name)

    def save(self, *args, **kwargs):
        if self.profile.user.user_type not in [COACH, MANAGEMENT]:
            raise InvalidUserTypeForOrganizationMemberError(_('Only a Coach account can be an organization member.'))

        # if (OrganizationMember.objects.filter(profile=self.profile).exclude(id=self.id).exists() or 
        #     Organizations.objects.filter(owner=self.profile).exclude(id=self.organization.id).exists()):
        #     raise ValidationError('This profile is already associated with an organization.')

        with transaction.atomic():
            # Lock the Organization row until the end of the transaction
            org = Organizations.objects.select_for_update().get(pk=self.organization.pk)

            # Count the number of members in the organization
            org_members_count = OrganizationMember.objects.filter(organization=org).count()
            
            # Check if the organization's subscription plan has a member limit
            if org.subscription_plan and org.subscription_plan.org_member_limit:
                org_member_limit = org.subscription_plan.org_member_limit

                # Check if the number of members exceeds the limit
                if org_members_count > org_member_limit:
                    raise OrganizationSizeLimitError(_("You can't signup and join Sport Organization, because the organization has reached its maximum member limit. please tell Organization owner, to increase the number of members allowed to organization."))

            super().save(*args, **kwargs)

class OrganizationInvite(models.Model):
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE)
    email = models.EmailField(max_length=300)
    already_user = models.BooleanField(default=False)
    invited = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    def __str__(self):
        return str(self.email + " " + self.organization.name + " " + self.invited.name)


    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(days=1)
        return timezone.now() > expiration_time

class OrganizationPhysicalAssessment(models.Model):
    OPA_TYPES = (
        ('time', _('Time')),
        ('score', _('Score')),
        ('distance', _('Distance')),
    )
    opa_title = models.CharField(max_length=70)
    assessment_type = models.CharField(max_length=10, choices=OPA_TYPES, default='score', db_index=True)
    best_score_lower = models.BooleanField(default=False, db_index=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, db_index=True)
    description = models.TextField(max_length=1500, blank=True, null=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.organization.name + ' ' + self.opa_title)
    

    
