from django.db.models.signals import post_save, post_delete

from users.models import User
from .models import Organizations, OrganizationInfo


def createOrganizationInfo(sender, instance, created, **kwargs):
    if created:
       organization = instance
       name = organization.name
       orgInfo = OrganizationInfo.objects.create(
           organization = organization,
           name = name
       )
       print('Org info created..', orgInfo)

def updateOrganizations(sender, instance, created, **kwargs):
    orgInfo = instance
    org = orgInfo.organization
    newOrgName = orgInfo.name

    if created == False:
        org.name = newOrgName
        org.save()

post_save.connect(createOrganizationInfo, sender=Organizations)
post_save.connect(updateOrganizations, sender=OrganizationInfo)
