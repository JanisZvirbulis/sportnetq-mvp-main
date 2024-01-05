from django.urls import path
from . import views

urlpatterns = [
    path('', views.organizations, name="organizations"),
    path('org/<str:pk>/', views.singleOrganization, name="single-org"),
    path('org/<str:pk>/invite/', views.invite_to_organization, name="org-invite"),
    path('org/<str:pk>/create-team/', views.createTeamForOrg, name="create-team-org"),
    path('org/<str:pk>/members/', views.orgMembers, name="org-members"),
    path('org/<str:pk>/members/edit/', views.editOrgMembers, name="edit-org-members"),
    path('org/<str:pk>/athetes/', views.browseOrgAthletes, name="browse-org-athletes"),
    path('org/<str:pk>/athete/<str:aid>/', views.browseOrgSingleAthlete, name="browse-single-athlete"),
    path('org/<str:pk>/teams/', views.browseOrgTeams, name="browse-org-teams"),
    path('org/<str:pk>/team/<str:tid>/', views.browseOrgSingleTeam, name="browse-single-team"),
    path('org/<str:pk>/settings/', views.orgSettings, name="org-settings"),
    path('org/<str:pk>/settings/physical-assessments/', views.allOrgPhysicalAssessment, name="all-org-pa"),
    path('org/<str:pk>/settings/physical-assessments/create/', views.createOrgPhysicalAssessment, name="create-org-pa"),
    path('org/<str:pk>/settings/physical-assessment/<str:id>/', views.viewOrgPhysicalAssessment, name="view-org-pa"),
    path('org/<str:pk>/settings/physical-assessments/<str:id>/edit/', views.editOrgPhysicalAssessment, name="edit-org-pa"),
    path('org/<str:pk>/settings/physical-assessments/<str:id>/delete/', views.deleteOrgPhysicalAssessment, name="delete-org-pa"),
    # path('invites/', views.userInvites, name="invites"),
    # path('accept-invite/<uuid:token>/', views.accept_invitation, name='accept-invitation'),
]
