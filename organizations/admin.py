from django.contrib import admin
from .models import Organizations, OrganizationInfo, OrganizationMember, OrgSubscriptionPlan, OrganizationInvite, OrganizationPhysicalAssessment

# Register your models here.
admin.site.register(Organizations)
admin.site.register(OrganizationMember)
admin.site.register(OrganizationInvite)
admin.site.register(OrganizationPhysicalAssessment)
admin.site.register(OrganizationInfo)
admin.site.register(OrgSubscriptionPlan)