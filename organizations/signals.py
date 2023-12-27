from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from users.models import User
from .models import Organizations, OrganizationMember, SubscriptionPlan


# def createOrganizationMeberRecordForOwner(sender, instance, created, **kwargs):
#    if created:
#     print('instance', instance)
#     organization = instance
#     member = OrganizationMember.objects.create(
#         profile = organization.owner,
#         organization = organization,
    
#     )
#     print('OrganizationMember record created', member)

# def create_new_organization(sender, instance, **kwargs):
#     # Get the subscription plan with code = 1
#     subscription_plan = SubscriptionPlan.objects.get(code=1)

#     # Create a new Organizations instance with the deleted profile as owner and assign the subscription_plan
#     new_organization = Organizations.objects.create(
#         name=f'Organization {instance.profile.name}',
#         owner=instance.profile,
#         subscription_plan=subscription_plan
#     )
#     print('New Organization record created', new_organization)


# post_save.connect(createOrganizationMeberRecordForOwner, sender=Organizations)
# post_delete.connect(create_new_organization, sender=OrganizationMember)