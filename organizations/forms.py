from django import forms
from django.forms import ModelForm
from datetime import datetime
import calendar
from .models import OrganizationInvite, OrganizationMember, OrganizationPhysicalAssessment ,org_role_choice, Owner
from teams.models import TeamSeason
from django.utils import timezone
from django.utils.translation import gettext as _

class InviteToOrgForm(ModelForm):
    class Meta:
        model = OrganizationInvite
        fields = [ 'email' ]

class OrgMemberForm(ModelForm):
    class Meta:
        model = OrganizationMember
        fields = [ 'org_role']
        widgets = {
            'org_role': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'org_role': _('Role'),
        }

    def __init__(self, *args, **kwargs):
        super(OrgMemberForm, self).__init__(*args, **kwargs)
        
        # Exclude the OWNER role choice
        self.fields['org_role'].choices = [(value, label) for value, label in org_role_choice if value != Owner]

class OrgPhysicalAssessmentForm(ModelForm):
    class Meta:
        model = OrganizationPhysicalAssessment
        fields = [ 'opa_title', 'assessment_type', 'best_score_lower', 'description']
        widgets = {
            'assessment_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'opa_title': _('Title'),
            'assessment_type': _('Type'),
            'best_score_lower': _('Best Score lower'),
            'description': _('Description'),
        }

class OrgTeamSeasonForm(forms.Form):
    last_day = calendar.monthrange(timezone.now().year, timezone.now().month)[1]
   
    def __init__(self, *args, **kwargs):
        team = kwargs.pop('team')
        initial_data = kwargs.pop('initial', {})
        super(OrgTeamSeasonForm, self).__init__(*args, **kwargs)
        self.fields['start_date'] = forms.DateField(
                label=_('Start Date'),
                widget=forms.DateInput(attrs={'type': 'date', 'class': 'datetimepicker-input'}),
                initial=timezone.now().replace(day=1).date(),
            )
        self.fields['end_date'] = forms.DateField(
                label=_('End Date'),
                widget=forms.DateInput(attrs={'type': 'date', 'class': 'datetimepicker-input'}),
                initial=timezone.now().replace(day=self.last_day).date(),
            )

    start_date = forms.DateField(label=_('Start Date'), required=True, widget=forms.DateInput(attrs={'type': 'date','class': 'datetimepicker-input'}))
    end_date = forms.DateField(label=_('End Date'), required=True, widget=forms.DateInput(attrs={'type': 'date', 'class': 'datetimepicker-input'}))

    
    def is_date_valid(self, field_name):
        cleaned_data = self.cleaned_data
        if field_name in cleaned_data:
            try:
                datetime.strptime(str(cleaned_data[field_name]), '%Y-%m-%d')
                return True
            except ValueError:
                return False
        return False
    

class orgAthleteTeamSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        teams = kwargs.pop('teams', [])
        super(orgAthleteTeamSelectForm, self).__init__(*args, **kwargs)
        self.fields['team'].choices = [('', _('All Teams'))] + [(str(team.teamID.id), team.teamID.teamName) for team in teams]

    team = forms.ChoiceField(label=_('Select Team'), required=False)

class orgAthletePATeamSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        teams = kwargs.pop('teams', [])
        super(orgAthletePATeamSelectForm, self).__init__(*args, **kwargs)
        self.fields['team'].choices = [('', _('All Teams'))] + [(str(team.teamID.id), team.teamID.teamName) for team in teams]

    team = forms.ChoiceField(label=_('Select Team'), required=False)

class orgAthleteAnalyticsTeamSelectForm(forms.Form):
    last_day = calendar.monthrange(timezone.now().year, timezone.now().month)[1]
    def __init__(self, *args, **kwargs):
        teams = kwargs.pop('teams', [])
        super(orgAthleteAnalyticsTeamSelectForm, self).__init__(*args, **kwargs)
        self.fields['team'].choices = [('', _('All Teams'))] + [(str(team.teamID.id), team.teamID.teamName) for team in teams]
         # Date fields
        self.fields['start_date'] = forms.DateField(
            label=_('Start Date'),
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'datetimepicker-input'}),
            initial=timezone.now().replace(day=1).date(),
        )
        self.fields['end_date'] = forms.DateField(
            label=_('End Date'),
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'datetimepicker-input'}),
            initial=timezone.now().replace(day=self.last_day).date(),
        )

    team = forms.ChoiceField(label=_('Select Team'), required=False)
    start_date = forms.DateField(label=_('Start Date'), required=True, widget=forms.DateInput(attrs={'type': 'date','class': 'datetimepicker-input'}))
    end_date = forms.DateField(label=_('End Date'), required=True, widget=forms.DateInput(attrs={'type': 'date', 'class': 'datetimepicker-input'}))

    

    def is_date_valid(self, field_name):
        cleaned_data = self.cleaned_data
        if field_name in cleaned_data:
            try:
                datetime.strptime(str(cleaned_data[field_name]), '%Y-%m-%d')
                return True
            except ValueError:
                return False
        return False