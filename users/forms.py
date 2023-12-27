
from django.forms import ModelForm, DateInput, BooleanField, CheckboxInput
from django.contrib.auth.forms import UserCreationForm
from users.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Profile


class CustomUserCreationForm(UserCreationForm):
    consent = BooleanField(
        required=True,
        label=_('I agree to the terms and conditions'),
        error_messages={'required': _('You must consent to sign up.')},
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password1', 'password2', 'consent', ]
        widgets = {
            'consent': CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
        }

        
    def clean(self):
        cleaned_data = super().clean()
        consent = cleaned_data.get('consent')

        if not consent:
            raise ValidationError(_('You must consent to sign up.'))

class CustomCoachCreationForm(UserCreationForm):
    consent = BooleanField(
        required=True,
        label=_('I agree to the terms and conditions'),
        error_messages={'required': _('You must consent to sign up.')},
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password1', 'password2', 'consent']
        widgets = {
            'consent': CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
        }

    def clean(self):
        cleaned_data = super().clean()
        consent = cleaned_data.get('consent')

        if not consent:
            raise ValidationError(_('You must consent to sign up.'))
        
class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'country', 'bio', 'profile_image', 'birth_date', 'gender_type']
        labels = {
            'name': _('First and last name'),
            'country': _('Country'),
            'profile_image': _('Profile image'),
            'bio': _('bio'),
            'birth_date': _('Birth Day'),
            'gender_type': _('Gender'),
        }
        widgets = {
            'birth_date': DateInput(attrs={'placeholder': 'Birth Day', 'class': 'datetimepicker-input'}),
        }
