from django import forms
from django.forms import ModelForm, DateInput, NumberInput, TimeInput, TextInput, CheckboxInput
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .models import Team, Event, AttendanceRecord, PhysicalAssessment, PhysicalAssessmentRecord, PhysicalAssessmentScore, Invitation, TeamMember, TeamSeason, TeamTactic, TacticImage, teamRoleChoice, AthleteInvitation, TeamNotification, NotificationLink, AthleteMarkForEvent, OrganizationPhysicalAssessmentRecord, OrganizationPhysicalAssessmentScore

EMPTYVALUE = '1'
ATTENDED = '2'
DIDNOTATTEND = '3'
SICK = '4'
INJURY = '5'
ATTENDANCE_CHOICES = (
    (EMPTYVALUE, '-----'),
    (ATTENDED, _('Attended')),
    (DIDNOTATTEND, _('Did not attend')),
    (SICK, _('Sick')),
    (INJURY, _('Injury')),
)

ATHLETE = '1'
COACH = '2'
STAFF = '3'
OWNER = '4'
teamRole = (
    (ATHLETE , _('Athlete')),
    (COACH, _('Coach')),
    (STAFF, _('Staff')),
    (OWNER, _('Owner')),
)


class TeamForm(ModelForm):
    # Generate a tuple of year choices from 1950 to 2050
    year_choices = [(year, year) for year in range(1950, 2051)]
    birth_year = forms.ChoiceField(
        choices=year_choices,
        required=False,
        label=_('Team/Athlete Year'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Team
        fields = ['teamName', 'teamSportType', 'description', 'birth_year', 'athlete_gender', 'country', 'team_image']
        labels = {
            'teamName': _('Team Name'),
            'teamSportType': _('Sport'),
            'description': _('Description'),
            'athlete_gender': _('Team Athlete Gender'),
            'birth_year': _('Team/Athlete Year'),
            'country': _('Country'),
            'team_image': _('Team Logo'),
        }

class TeamMemberForm(ModelForm):
    class Meta:
        model = TeamMember
        fields = ['number', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'role': _('Team Role'),
        }

    def __init__(self, *args, **kwargs):
        super(TeamMemberForm, self).__init__(*args, **kwargs)
        
        # Exclude the OWNER role choice
        self.fields['role'].choices = [(value, label) for value, label in teamRoleChoice if value != OWNER]

class CreateEventForm(ModelForm):
    RECUR_CHOICES = [
        ('none', 'No Recurrence'),
        ('weekly', 'Weekly'),
    ]
    recurrence = forms.ChoiceField(choices=RECUR_CHOICES, required=False)
    recurrence_end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'class': 'datetimepicker-input'}))

    class Meta:
        model = Event
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TextInput(attrs={'class': 'datetimepicker-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control'}),
            'send_email_notification': CheckboxInput(attrs={'class': 'checkbox-input'}),
            'email_notification': forms.Select(attrs={'class': 'form-control'}),
        }
        fields = ['title', 'type', 'start_time', 'recurrence', 'recurrence_end_date', 'send_email_notification', 'email_notification', 'comment']
        labels = {
            'title': _('Title'),
            'type': _('Type'),
            'start_time': _('Start time'),
            'comment': _('Comment'),
            'send_email_notification': _('Send email notification'),
            'email_notification': _('Notification template'),
        }

    def __init__(self, *args, **kwargs):
        notifications = kwargs.pop('notifications', None)
        # Initialize the form once
        super(CreateEventForm, self).__init__(*args, **kwargs)
        # Set input formats and translated placeholders
        self.fields['recurrence_end_date'].widget = forms.TextInput(attrs={'class': 'datetimepicker', 'type': 'date'})
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.set_translated_placeholders()
        self.fields['recurrence_end_date'].widget.attrs['placeholder'] = _('Recurring events can be scheduled up to 3 months in advance from the start date')
        # Set choices for the 'email_notification' field
        choices = [(None, '---------')]  # Add an empty choice
        if notifications is not None:
            choices += [(n.id, f'{n.title}') for n in notifications]
        self.fields['email_notification'].choices = choices
        # Set initial values and labels for manually added fields
        self.fields['recurrence'].initial = 'none'
        self.fields['recurrence'].label = _('Recurrence')
        self.fields['recurrence_end_date'].label = _('Recurrence End Date')

    def clean(self):
        cleaned_data = super().clean()
        send_email_notification = cleaned_data.get('send_email_notification')
        email_notification = cleaned_data.get('email_notification')
        if send_email_notification and not email_notification:
            raise forms.ValidationError(_('If sending email notification is enabled, a notification template must be selected.'))

        return cleaned_data
    
    def set_translated_placeholders(self):
        for field_name, field in self.fields.items():
            if field.label is not None:
                field.label = _(field.label)
            if 'placeholder' not in self.fields[field_name].widget.attrs:
                placeholder_label = self.fields[field_name].label
                self.fields[field_name].widget.attrs['placeholder'] = placeholder_label



class EventForm(ModelForm):
    class Meta:
        model = Event
        # datetime-local is an HTML5 input type, format to make datetime show on fields
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TextInput(attrs={'class': 'datetimepicker-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control'}),
            'send_email_notification': CheckboxInput(attrs={'class': 'checkbox-input'}),
            'email_notification': forms.Select(attrs={'class': 'form-control'}),

        }
        fields = ['title', 'type', 'start_time', 'comment', 'send_email_notification', 'email_notification']
        labels = {
            'title': _('Title'),
            'type': _('Type'),
            'start_time': _('Start time'),
            'comment': _('Comment'),
            'send_email_notification': _('Send email notification'),
            'email_notification': _('Notification template'),
        }

    def __init__(self, *args, **kwargs):
        notifications = kwargs.pop('notifications', None)
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.set_translated_placeholders()

        choices = [(None, '---------')]  # Add an empty choice
        if notifications is not None:
            choices += [(n.id, f'{n.title}') for n in notifications]

        self.fields['email_notification'].choices = choices

        # if notifications is not None:
        #     self.fields['email_notification'].choices = [(n.id, f'{n.title}') for n in notifications]

    def clean(self):
        cleaned_data = super().clean()
        send_email_notification = cleaned_data.get('send_email_notification')
        email_notification = cleaned_data.get('email_notification')

        if send_email_notification and not email_notification:
            raise forms.ValidationError(_('If sending email notification is enabled, a notification template must be selected.'))

        return cleaned_data
    

    def set_translated_placeholders(self):
        for field_name, field in self.fields.items():
            field.label = _(field.label)  # Translating the field label
            if 'placeholder' not in self.fields[field_name].widget.attrs:
                placeholder_label = self.fields[field_name].label
                self.fields[field_name].widget.attrs['placeholder'] = placeholder_label
    
    
        


class AttendanceRecordForm(ModelForm):
    class Meta:
        model = AttendanceRecord
        widgets = {
            'attendance': forms.Select(choices=AttendanceRecord.ATTENDANCE_CHOICES, attrs={'class': 'form-select'}),
            'short_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        fields = ['attendance', 'short_note',]
        labels = {
            'attendance': '',
            'short_note': _('Note'),
        }


class AddAttendanceRecordForm(ModelForm):
    class Meta:
        model = AttendanceRecord
        widgets = {'team_member': forms.Select()}
        fields = ['team_member']
        labels = {
            'team_member': _('Team Athlete'),
        }

    def __init__(self, *args, **kwargs):
        team_members = kwargs.pop('team_members', None)
        super().__init__(*args, **kwargs)
        if team_members is not None:
            # Note: It's important that team_members was fetched with select_related('profileID')
            # so that we don't hit the database again for each profile.
            self.fields['team_member'].choices = [(tm.profileID.id, f'{tm.profileID.name}') for tm in team_members]

class AthleteMarkForEventForm(ModelForm):
    class Meta:
        model = AthleteMarkForEvent
        fields = ['mark']


class PhysicalAssessmentForm(ModelForm):
    class Meta:
        model = PhysicalAssessment
        fields = [ 'physical_assessment_title', 'assessment_type', 'best_score_lower' ]
        labels = {
            'physical_assessment_title': _('Title'),
            'assessment_type': _('Type'),
            'best_score_lower': _('Best Score lower'),
        }
class PhysicalAssessmentRecordForm(ModelForm):
    class Meta:
        model = PhysicalAssessmentRecord
        fields = ['physical_assessment_date',]
        labels = {
            'physical_assessment_date': _('Date'),
        }
        widgets = {
            'physical_assessment_date': DateInput(attrs={'placeholder': _('Date'), 'class': 'datetimepicker-input'}),
            # 'physical_assessment_date': DateInput(
            #     format='%D-%M-%Y',
            #     attrs={'type': 'date', 'class': 'form-control'}
            # ),
        }

class CustomTimeInput(TimeInput):
    format_key = 'TIME_INPUT_FORMATS'

    def format_value(self, value):
        # format the time value as you want here
        if value:
            # Ensure that the value has microseconds before slicing
            if '.' in value:
                value = value[:value.index('.')+4]  # keep 3 digits after the dot
        return value
    
class PhysicalAssessmentScoreForm(ModelForm):
    class Meta:
        model = PhysicalAssessmentScore
        fields = [ 'score', 'time', 'distance',]
        widgets = {
            'score': NumberInput(),
            'time': CustomTimeInput(),
            'distance': NumberInput(),
        }
        labels = {
            'score': _('Score'),
            'time': _('Time'),
            'distance': _('Distance'),
        }

class AddTeamMemberScoreToPhysicalAssessmentRecord(forms.ModelForm):
    class Meta:
        model = PhysicalAssessmentScore
        widgets = {'team_member': forms.Select()}
        fields = ['team_member']
        labels = {
            'team_member': _('Team Athlete'),
        }


    def __init__(self, *args, **kwargs):
        team_members = kwargs.pop('team_members', None)
        super().__init__(*args, **kwargs)
        if team_members is not None:
            # Note: It's important that team_members was fetched with select_related('profileID')
            # so that we don't hit the database again for each profile.
            self.fields['team_member'].choices = [(tm.profileID.id, f'{tm.profileID.name}') for tm in team_members]

class OrgAddTeamMemberScoreToPhysicalAssessmentRecord(forms.ModelForm):
    class Meta:
        model = OrganizationPhysicalAssessmentScore
        widgets = {'team_member': forms.Select()}
        fields = ['team_member']
        labels = {
            'team_member': _('Team Athlete'),
        }


    def __init__(self, *args, **kwargs):
        team_members = kwargs.pop('team_members', None)
        super().__init__(*args, **kwargs)
        if team_members is not None:
            # Note: It's important that team_members was fetched with select_related('profileID')
            # so that we don't hit the database again for each profile.
            self.fields['team_member'].choices = [(tm.profileID.id, f'{tm.profileID.name}') for tm in team_members]


class OrgPhysicalAssessmentRecordForm(ModelForm):
    class Meta:
        model = OrganizationPhysicalAssessmentRecord
        fields = ['org_physical_assessment_date',]
        labels = {
            'org_physical_assessment_date': _('Date'),
        }
        widgets = {
            'org_physical_assessment_date': DateInput(attrs={'placeholder': _('Date'), 'class': 'datetimepicker-input'}),
            # 'physical_assessment_date': DateInput(
            #     format='%D-%M-%Y',
            #     attrs={'type': 'date', 'class': 'form-control'}
            # ),
        }

class OrgPhysicalAssessmentScoreForm(ModelForm):
    class Meta:
        model = OrganizationPhysicalAssessmentScore
        fields = [ 'score', 'time', 'distance',]
        widgets = {
            'score': NumberInput(),
            'time': CustomTimeInput(),
            'distance': NumberInput(),
        }
        labels = {
            'score': _('Score'),
            'time': _('Time'),
            'distance': _('Distance'),
        }

class TacticImageForm(forms.ModelForm):
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-input'}))
    class Meta:
        model = TacticImage
        fields = ('image', 'description', 'play')
        labels = {
            'image': _('Image'),
            'description': _('Description'),
            'play': _('Plays sequence number'),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image', False)
        if image: 
            return image
        if self.instance.pk and self.instance.image:  # check if TacticImage instance exists and has an image
            return self.instance.image  # if so, return the existing image
        raise forms.ValidationError(_("Image field is required."))  # if not, raise an error


class TacticForm(forms.ModelForm):
    class Meta:
        model = TeamTactic
        fields = ['title', 'public',]
        labels = {
            'title': _('Name of Tactic'),
            'public': _('Visible for athletes'),
        }


# class TacticForm(forms.ModelForm):
#     shared_with_teams = forms.ModelMultipleChoiceField(
#         queryset=Team.objects.none(),
#         label='Share with teams'
#     )

#     class Meta:
#         model = TeamTactic
#         fields = ['title', 'public', 'shared_with_teams']
#         labels = {
#             'title': 'Name of Tactic',
#             'public': 'Visible for athletes',
#         }

#     def __init__(self, *args, user=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         if user is not None:
#             self.fields['shared_with_teams'].queryset = Team.objects.filter(teammember__profileID=user, teammember__role__in=['1', '2'])

TacticImageFormSet = forms.inlineformset_factory(TeamTactic, TacticImage, form=TacticImageForm, extra=1, can_delete=True)

class InvitationForm(ModelForm):
    class Meta:
        model = Invitation
        fields = [ 'email' ]
        labels = {
             'email': _('E-mail'),
        }

class AthleteInvitationForm(ModelForm):
    class Meta:
        model = AthleteInvitation
        fields = [ 'email']
        labels = {
             'email': _('E-mail'),
        }

class SingleTeamSeasonForm(ModelForm):
    class Meta:
        model = TeamSeason
        fields = [ 'start_date', 'end_date', 'current_season']
        widgets = {
            'start_date': TextInput(attrs={'placeholder': 'Season start date', 'class': 'datetimepicker-input'}),
            'end_date': TextInput(attrs={'placeholder': 'Season end date', 'class': 'datetimepicker-input'}),
            'current_season': CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
        labels = {
             'start_date': _('Start date'),
             'end_date': _('End date'),
             'current_season': _('Current season'),

        }

    def save(self, commit=True):
        try:
            instance = super().save(commit=False)
            if commit:
                instance.save()
            return instance
        except ValidationError as e:
            self.add_error(None, e)

class TeamSeasonForm(forms.Form):
    team_season = forms.ModelChoiceField(
        queryset=None,
        label= _('Select Team Season'),
        widget=forms.Select(attrs={'onchange': 'submit();'}),
    )

    def __init__(self, *args, **kwargs):
        team = kwargs.pop('team')
        current_season = kwargs.pop('current_season', None)  # Accept current_season argument
        super(TeamSeasonForm, self).__init__(*args, **kwargs)
        self.fields['team_season'] = forms.ModelChoiceField(
            queryset=TeamSeason.objects.filter(team=team).order_by('start_date'),
            required=False,
            initial=current_season,  # Use the passed current_season as initial value
            empty_label=_("ALL RECORDS"),
            widget=forms.Select(attrs={'class': 'form-select'})
        )

class PhysicalAssessmentChoiceForm(forms.Form):
    pa_dates = forms.ModelChoiceField(
        queryset=None,
        label= _('Select date to edit records'), 
        )
    
    def __init__(self, *args, **kwargs):
        pa = kwargs.pop('parecords', None)
        super(PhysicalAssessmentChoiceForm, self).__init__(*args, **kwargs)
        self.fields['pa_dates'] = forms.ModelChoiceField(
            queryset=pa,
            required=False,
            empty_label=_("Select date to edit records"),
            widget=forms.Select(attrs={'class': 'form-select-pa'})
        )
        self.fields['pa_dates'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        return obj.physical_assessment_date.strftime("%d-%m-%Y")


class OrgPhysicalAssessmentChoiceForm(forms.Form):
    pa_dates = forms.ModelChoiceField(
        queryset=None,
        label= _('Select date to edit records'), 
        )
    
    def __init__(self, *args, **kwargs):
        pa = kwargs.pop('parecords', None)
        super(OrgPhysicalAssessmentChoiceForm, self).__init__(*args, **kwargs)
        self.fields['pa_dates'] = forms.ModelChoiceField(
            queryset=pa,
            required=False,
            empty_label=_("Select date to edit records"),
            widget=forms.Select(attrs={'class': 'form-select-pa'})
        )
        self.fields['pa_dates'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        return obj.org_physical_assessment_date.strftime("%d-%m-%Y")

# class EmailNotificationForm(ModelForm):
#     class Meta:
#         model = TeamNotification
#         fields = [ 'title', 'message', 'link_field']
#         widgets = {
#             'title': TextInput(attrs={'placeholder': 'Notification name'}),
#             'message': TextInput(attrs={'placeholder': 'Add text for your E-mail notification'}),
#             'link_field': TextInput(attrs={'placeholder': 'Please add full URL link, which starts with https:// or http://'}),
    
#         }
#         labels = {
#              'title': _('Title'),
#              'message': _('Notification Message'),
#              'link_field': _('URL Link'),

#         }

class EmailNotificationForm(ModelForm):
    links = forms.ModelMultipleChoiceField(
        queryset=NotificationLink.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = TeamNotification
        fields = ['title', 'message', 'links']

    def __init__(self, *args, **kwargs):
        team_id = kwargs.pop('team_id', None)
        super(EmailNotificationForm, self).__init__(*args, **kwargs)

        if team_id:
            self.fields['links'].queryset = NotificationLink.objects.filter(team_id=team_id)

class TeamNotificationLinkForm(ModelForm):
    class Meta:
        model = NotificationLink
        fields = ['title', 'url']
        widgets = {
            'title': TextInput(attrs={'placeholder': 'Notification Link Name'}),
            'url': TextInput(attrs={'placeholder': 'Please add full URL link, which starts with https:// or http://'}),
        }
        labels = {
            'title': _('Title'),
            'url': _('URL Link'),
        }