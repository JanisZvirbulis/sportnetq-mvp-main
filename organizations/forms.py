from django import forms
from django.forms import ModelForm
from .models import OrganizationInvite, OrganizationMember, org_role_choice, Owner
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

