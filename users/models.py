from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.crypto import get_random_string
from django.utils import timezone
from PIL import Image
from io import BytesIO
import uuid

# Create your models here.
def profile_image_upload_path(instance, filename):
    return f"profiles/{instance.id}/{filename}"

ATHLETE = '1'
COACH = '2'
# SCOUT = '3'
MANAGEMENT = '3'

MALE = '1'
FEMALE = '2'


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

class User(AbstractUser):
    email = models.EmailField(unique=True)
    id = models.UUIDField(default=uuid.uuid4 ,unique=True, primary_key=True, editable=False)
    USER_TYPE_CHOICES = (
        (ATHLETE , 'Athlete'),
        (COACH, 'Coach'),
    )

    
    user_type = models.CharField(
        max_length=6,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_CHOICES[0][0],
    )
    created = models.DateTimeField(auto_now_add=True)
    consent = models.BooleanField(default=False)

    def __str__(self):
        return str(self.first_name + " " + self.last_name + " " + self.user_type)
    


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=300, null=True, blank=True, unique=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        default='LV',
    )

    bio = models.TextField(max_length=2000, blank=True, null=True)
    profile_image = models.ImageField(null=True, blank=True, upload_to=profile_image_upload_path, default='profiles/user-default.jpeg', max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4 ,unique=True, primary_key=True, editable=False)


    GENDER_TYPE_CHOICES = (
        (MALE , _('Male')),
        (FEMALE, _('Female'))
    )

    gender_type = models.CharField(
        max_length=2,
        choices=GENDER_TYPE_CHOICES,
        default=GENDER_TYPE_CHOICES[0][0],
    )

    def __str__(self):
        return str(self.user.first_name + " " + self.user.last_name)
    
    # def save(self, *args, **kwargs):
    #     super(Profile, self).save(*args, **kwargs)

    #     if not self.profile_image:
    #         self.profile_image = 'profiles/user-default.jpeg'
    #     else:
    #         # Open the uploaded image
    #         img = Image.open(self.profile_image.path)
    #         # If the image has an alpha channel, convert it to RGB
    #         if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
    #             img = img.convert('RGB')

    #         # Set the desired size (width, height)
    #         desired_size = (300, 300)
    #         img.thumbnail(desired_size, Image.ANTIALIAS)

    #         # Save the resized image to a BytesIO object
    #         output = BytesIO()
    #         img.save(output, format='JPEG', quality=90)
    #         output.seek(0)

    #         if self.profile_image.name:
    #             filename = f"{self.profile_image.name.split('.')[0]}.jpeg"
    #         else:
    #             filename = 'profiles/user-default.jpeg'

    #         # Replace the original image with the resized one
    #         self.profile_image.delete(save=False)  # Delete the original image
    #         self.profile_image = InMemoryUploadedFile(
    #             output,
    #             'ImageField',
    #             filename,
    #             'image/jpeg',
    #             output.getbuffer().nbytes,
    #             None
    #         )

    #     super(Profile, self).save(*args, **kwargs)  # Save the model with the resized image


    @property
    def imageURL(self):
        try:
            url = self.profile_image.url
        except:
            url = ''
        return url


        


