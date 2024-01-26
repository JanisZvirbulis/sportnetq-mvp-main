from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from io import BytesIO
import uuid
from users.models import Profile
from organizations.models import Organizations, OrganizationMember, OrganizationPhysicalAssessment

def team_image_upload_path(instance, filename):
    return f"teams/{instance.id}/{filename}"

def team_tactic_image_upload_path(instance, filename):
    return f"teams/{instance.team_tactic.team.id}/playbook/{filename}"

# enums #
# sportChoice ######################################
BASKETBALL = '1'
FOOTBALL = '2'
ICEHOCKEY = '3'
VOLLEYBALL = '4'
FLOORBALL = '5'
OTHER_SPORT = '6'
sportChoice = (
    (BASKETBALL , _('Basketball')),
    (FOOTBALL, _('Football')),
    (ICEHOCKEY, _('Hockey')),
    (VOLLEYBALL, _('Volleyball')),
    (FLOORBALL, _('Floorball')),
    (OTHER_SPORT, _('Other Sport'))
)
# CountryChoice ######################################
COUNTRY_CHOICES = (
    ('AL', _('Albania')),
    ('AD', _('Andorra')),
    ('AT', _('Austria')),
    ('BY', _('Belarus')),
    ('BE', _('Belgium')),
    ('BA', _('Bosnia and Herzegovina')),
    ('BG', _('Bulgaria')),
    ('CA', _('Canada')),
    ('HR', _('Croatia')),
    ('CY', _('Cyprus')),
    ('CZ', _('Czech Republic')),
    ('DK', _('Denmark')),
    ('EE', _('Estonia')),
    ('FO', _('Faroe Islands')),
    ('FI', _('Finland')),
    ('FR', _('France')),
    ('DE', _('Germany')),
    ('GI', _('Gibraltar')),
    ('GR', _('Greece')),
    ('GG', _('Guernsey')),
    ('HU', _('Hungary')),
    ('IS', _('Iceland')),
    ('IE', _('Ireland')),
    ('IT', _('Italy')),
    ('JE', _('Jersey')),
    ('LV', _('Latvia')),
    ('LI', _('Liechtenstein')),
    ('LT', _('Lithuania')),
    ('LU', _('Luxembourg')),
    ('MK', _('North Macedonia')),
    ('MT', _('Malta')),
    ('MD', _('Moldova')),
    ('MC', _('Monaco')),
    ('ME', _('Montenegro')),
    ('NL', _('Netherlands')),
    ('NO', _('Norway')),
    ('PL', _('Poland')),
    ('PT', _('Portugal')),
    ('RO', _('Romania')),
    ('RU', _('Russia')),
    ('SM', _('San Marino')),
    ('RS', _('Serbia')),
    ('SK', _('Slovakia')),
    ('SI', _('Slovenia')),
    ('ES', _('Spain')),
    ('SE', _('Sweden')),
    ('CH', _('Switzerland')),
    ('UA', _('Ukraine')),
    ('GB', _('United Kingdom')),
    ('US', _('United States')),
)

# teamRole ######################################
ATHLETE = '1'
COACH = '2'
STAFF = '3'
OWNER = '4'
teamRoleChoice = (
    (ATHLETE , _('Athlete')),
    (COACH, _('Coach')),
    (STAFF, _('Staff')),
    (OWNER, _('Owner')),
)


# eventChoice ######################################
PRACTICE = '1'
GAME = '2'
TRAININGCAMP = '3'
OTHER_EVENT = '4'
eventChoice = (
    (PRACTICE, _('Practice')),
    (GAME, _('Game')),
    (TRAININGCAMP, _('Training Camp')),
    (OTHER_EVENT, _('Other')),
)

MALE = '1'
FEMALE = '2'
NOT_REQUIRED = '3'
athleteGenderChoice = (
    (MALE, _('Male')),
    (FEMALE, _('Female')),
    (NOT_REQUIRED, _('Not Required')),
)

# Create your models here.
class Team(models.Model):
    teamSportType = models.CharField(
        max_length=2,
        choices=sportChoice,
        default=sportChoice[0][0], 
        db_index=True,
    )
    teamName = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    team_members = models.ManyToManyField(Profile, related_name="team_members", through="TeamMember", db_index=True)
    team_image = models.ImageField(null=True, blank=True, upload_to=team_image_upload_path, default='teams/blank-team.jpeg')
    organization = models.ForeignKey(Organizations ,on_delete=models.CASCADE, db_index=True)
    athlete_gender = models.CharField(
        max_length=2,
        choices=athleteGenderChoice,
        default=athleteGenderChoice[2][0], 
        db_index=True,
    )
    birth_year = models.IntegerField(validators=[MinValueValidator(1950), MaxValueValidator(2050)], blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    owner = models.ForeignKey(OrganizationMember, on_delete=models.CASCADE, db_index=True)
    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        default='LV',
    )


    def __str__(self):
        return str(self.teamName)

    @property
    def imageURL(self):
        try:
            url = self.team_image.url
        except:
            url = ''
        return url
    
class TeamMember(models.Model):
    profileID = models.ForeignKey(Profile, on_delete=models.CASCADE, db_index=True)
    teamID = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(
        max_length=2,
        choices=teamRoleChoice,
        default=teamRoleChoice[0][0],
        db_index=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    number = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], blank=True, null=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    class Meta:
        unique_together = ('profileID', 'teamID')

    def __str__(self):
        return str(self.teamID.teamName + ' ' + self.profileID.name + ' ' + self.role)
    
    
class TeamNotification(models.Model):
    title = models.CharField(max_length=140)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    message = models.TextField(max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    links = models.ManyToManyField("NotificationLink", blank=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return str(self.team.teamName + ' : ' + self.title)
    
class NotificationLink(models.Model):
    title = models.CharField(max_length=140)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return self.title
    
    
class Event(models.Model):
    title = models.CharField(max_length=200, blank=True)
    teamID = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='events', db_index=True)
    type= models.CharField(
        max_length=2,
        choices=eventChoice,
        default=eventChoice[0][0],
        db_index=True,
    )
    location = models.CharField(max_length=70, blank=True, null=True)
    start_time = models.DateTimeField(db_index=True)
    comment = models.TextField(max_length=2000, blank=True, null=True)
    send_email_notification = models.BooleanField(default=False, db_index=True)
    email_notification = models.ForeignKey(TeamNotification, on_delete=models.SET_NULL, blank=True, null=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)


    @property
    def get_html_url(self):
        url = str(self.id) + '/'
        time_str = datetime.strftime(self.start_time, '%H:%M')
        return f'<a href="{url}"> {self.get_type_display()} {time_str}</a>'
    

    def __str__(self):
        return str(self.teamID.teamName + ' ' + self.type + ' ' + self.title)

#  event attendance record
class AttendanceRecord(models.Model):
    EMPTYVALUE = '1'
    ATTENDED = '2'
    DIDNOTATTEND = '3'
    ILL = '4'
    INJURY = '5'
    NOT_REQUIRED = '6'
    OTHER_ATTENDANCE = '7'
    ATTENDANCE_CHOICES = (
        (EMPTYVALUE, '-----'),
        (ATTENDED, _('Attended')),
        (DIDNOTATTEND, _('Did not attend')),
        (ILL, _('ill')),
        (INJURY, _('Injury')),
        (NOT_REQUIRED, _('Not required')),
        (OTHER_ATTENDANCE, _('Other')),
    )
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    attendance = models.CharField(
        max_length=2,
        choices=ATTENDANCE_CHOICES,
        default=EMPTYVALUE,
        db_index=True
    )
    email_notification_sent = models.BooleanField(default=False, db_index=True)
    short_note = models.TextField(max_length=500, blank=True, null=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team_member', 'event', 'team')

    def __str__(self):
        return str(self.team_member.profileID.name)


#  Physical Assessment models
class PhysicalAssessment(models.Model):
    PHYSICAL_ASSESSMENT_TYPES = (
        ('time', _('Time')),
        ('score', _('Score')),
        ('distance', _('Distance')),
    )
    physical_assessment_title = models.CharField(max_length=70)
    assessment_type = models.CharField(max_length=10, choices=PHYSICAL_ASSESSMENT_TYPES, default='score', db_index=True)
    best_score_lower = models.BooleanField(default=False, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.team.teamName + ' ' + self.physical_assessment_title)

class PhysicalAssessmentRecord(models.Model):
    physical_assessment = models.ForeignKey(PhysicalAssessment, on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    physical_assessment_date = models.DateField(db_index=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.team.teamName + ' ' + self.physical_assessment.physical_assessment_title + ' ' + str(self.physical_assessment_date))
    
    class Meta:
        unique_together = ('physical_assessment', 'team', 'physical_assessment_date')


class PhysicalAssessmentScore(models.Model):
    score = models.FloatField(null=True, blank=True, db_index=True)
    time = models.DurationField(null=True, blank=True, db_index=True)
    distance = models.FloatField(null=True, blank=True, db_index=True)
    physical_assessment = models.ForeignKey(PhysicalAssessment, on_delete=models.CASCADE, db_index=True)
    physical_assessment_record = models.ForeignKey(PhysicalAssessmentRecord, on_delete=models.CASCADE, db_index=True)
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('physical_assessment', 'physical_assessment_record', 'team_member', 'team')


    def clean(self):
        assessment_type = self.physical_assessment.assessment_type

        if assessment_type == 'score':
            if self.score is None:
                raise ValidationError(_("Score must be filled in when assessment_type is 'score'."))
            if self.time is not None or self.distance is not None:
                raise ValidationError(_("Only the score field can be filled in when assessment_type is 'score'."))
        elif assessment_type == 'time':
            if self.time is None:
                raise ValidationError(_("Time must be filled in when assessment_type is 'time'."))
            if self.score is not None or self.distance is not None:
                raise ValidationError(_("Only the time field can be filled in when assessment_type is 'time'."))
        elif assessment_type == 'distance':
            if self.distance is None:
                raise ValidationError(_("Distance must be filled in when assessment_type is 'distance'."))
            if self.score is not None or self.time is not None:
                raise ValidationError(_("Only the distance field can be filled in when assessment_type is 'distance'."))
        else:
            raise ValidationError(_("Invalid assessment_type."))
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.team.teamName + ' ' + self.physical_assessment.physical_assessment_title + ' ' + self.team_member.profileID.name + ' ' + str(self.physical_assessment_record.physical_assessment_date))


class OrganizationPhysicalAssessmentRecord(models.Model):
    org_physical_assessment = models.ForeignKey(OrganizationPhysicalAssessment, on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, db_index=True)
    org_physical_assessment_date = models.DateField(db_index=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.organization.name + ' : Team-> ' + self.team.teamName + ' ' + self.org_physical_assessment.opa_title + ' ' + str(self.org_physical_assessment_date))
    
    class Meta:
        unique_together = ('org_physical_assessment', 'team', 'org_physical_assessment_date', 'organization')


class OrganizationPhysicalAssessmentScore(models.Model):
    score = models.FloatField(null=True, blank=True, db_index=True)
    time = models.DurationField(null=True, blank=True, db_index=True)
    distance = models.FloatField(null=True, blank=True, db_index=True)
    org_physical_assessment = models.ForeignKey(OrganizationPhysicalAssessment, on_delete=models.CASCADE, db_index=True)
    org_physical_assessment_record = models.ForeignKey(OrganizationPhysicalAssessmentRecord, on_delete=models.CASCADE, db_index=True)
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, db_index=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('org_physical_assessment', 'org_physical_assessment_record', 'team_member', 'team', 'organization')


    def clean(self):
        assessment_type = self.org_physical_assessment.assessment_type

        if assessment_type == 'score':
            if self.score is None:
                raise ValidationError(_("Score must be filled in when assessment_type is 'score'."))
            if self.time is not None or self.distance is not None:
                raise ValidationError(_("Only the score field can be filled in when assessment_type is 'score'."))
        elif assessment_type == 'time':
            if self.time is None:
                raise ValidationError(_("Time must be filled in when assessment_type is 'time'."))
            if self.score is not None or self.distance is not None:
                raise ValidationError(_("Only the time field can be filled in when assessment_type is 'time'."))
        elif assessment_type == 'distance':
            if self.distance is None:
                raise ValidationError(_("Distance must be filled in when assessment_type is 'distance'."))
            if self.score is not None or self.time is not None:
                raise ValidationError(_("Only the distance field can be filled in when assessment_type is 'distance'."))
        else:
            raise ValidationError(_("Invalid assessment_type."))
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.organization.name + ' : Team-> ' + self.team.teamName + ' ' + self.org_physical_assessment.opa_title + ' ' + self.team_member.profileID.name + ' ' + str(self.org_physical_assessment_record.org_physical_assessment_date))


class TeamSeason(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    current_season = models.BooleanField(default=False, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        if self.current_season:
            return _('SEASON') + ' ' + str(self.start_date) + ' - ' + str(self.end_date) + ' (' + _('active season') + ')'
        else:
            return _('SEASON') + ' ' + str(self.start_date) + ' - ' + str(self.end_date)
    def clean(self):
        if self.start_date is None or self.end_date is None:
            raise ValidationError(_("Start date and end date must be provided."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)  # Save the current instance first
        if self.current_season:
            self.set_current_season()  # Update other instances after saving the current instance

    def set_current_season(self):
    # Set all other TeamSeason instances with the same team to current_season=False
        TeamSeason.objects.filter(team=self.team, current_season=True).exclude(id=self.id).update(current_season=False)
    # No need to update the current instance, as it was already saved with current_season=True

class TeamTactic(models.Model):
    title = models.CharField(max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_index=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False, db_index=True)

class TacticImage(models.Model):
    team_tactic = models.ForeignKey(TeamTactic, related_name='tactic_images', on_delete=models.CASCADE, db_index=True)
    play = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(15)], default=1)
    image = models.ImageField(upload_to=team_tactic_image_upload_path)
    description = models.TextField()
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:  # renamed from 'team_image' to 'image' for consistency
            img = Image.open(self.image)

            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')

            desired_size = (800, 600)
            img.thumbnail(desired_size, Image.ANTIALIAS)

            output = BytesIO()
            img.save(output, format='JPEG', quality=95)
            output.seek(0)

            self.image = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{self.image.name.split('.')[0]}.jpeg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
        super().save(*args, **kwargs)

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
    


class Invitation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    email = models.EmailField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    

    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(days=1)
        return timezone.now() > expiration_time
    
class AthleteInvitation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    email = models.EmailField(max_length=300)
    invited_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(days=1)
        return timezone.now() > expiration_time
    
    def __str__(self):
        return str(self.team.teamName + ' ' + self.invited_by.name + ' invited ' + self.email)

class AthleteMarkForEvent(models.Model):

    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_index=True)
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, db_index=True)
    mark = models.PositiveIntegerField(default=7,validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return str(self.member + ' :  scrore: ' + str(self.mark) + ' ' + self.event)
  