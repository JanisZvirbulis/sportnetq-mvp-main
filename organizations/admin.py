from django.contrib import admin
from .models import Organizations, OrganizationMember, SubscriptionPlan, OrganizationInvite, OrganizationPhysicalAssessment

# Register your models here.
admin.site.register(Organizations)
admin.site.register(OrganizationMember)
admin.site.register(SubscriptionPlan)
admin.site.register(OrganizationInvite)
admin.site.register(OrganizationPhysicalAssessment)