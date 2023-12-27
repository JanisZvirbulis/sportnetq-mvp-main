
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from users.models import User
from .models import Profile, ATHLETE



#@receiver(post_save, sender=Profile)
def createProfile(sender, instance, created, **kwargs):
   if created:
    print('instance', instance)
    user = instance
    email = user.email.lower().strip()
    profile = Profile.objects.create(
        user = user,
        username = user.username,
        email = email,
        name = user.first_name + " " + user.last_name,
    )
    print('profile created..', profile)
 

# def createProfileRole(sender, instance, created, **kwargs):
#    if created:
#       profile = instance
#       profileRole = ProfileRole.objects.create(
#         profile = profile,
#         user_type = '1'
#       )
#       print('profileRole created..', profileRole)

def updateUser(sender, instance, created, **kwargs):
    profile = instance
    first_name, _ = profile.name.strip().split(" ", 1)
    user = profile.user
    email = profile.email.lower().strip()

    if created == False:
        user.name = first_name
        user.username = profile.username
        user.email = email
        user.save()

def deleteUser(sender, instance, **kwargs):
    try:
        user = instance.user
        user.delete()
        print('Deleting user..')
    except:
        pass





post_save.connect(createProfile, sender=User)
# post_save.connect(createProfileRole, sender=Profile)
post_save.connect(updateUser, sender=Profile)
# post_save.connect(updateProfile, sender=User)
post_delete.connect(deleteUser, sender=Profile)