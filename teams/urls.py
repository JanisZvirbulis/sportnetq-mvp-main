from django.urls import path
from . import views

urlpatterns = [
    path('', views.teams, name="teams"),
    path('team/<str:pk>/', views.team, name="team"),

    #  team setings
    path('team/<str:pk>/settings/', views.teamSettings, name="team-settings"),
    path('team/<str:pk>/settings/notifications/', views.allEmailNotifications, name="email-notifications"),
    path('team/<str:pk>/settings/notifications/add/', views.createEmailNotification, name="add-email-notification"),
    path('team/<str:pk>/settings/notifications/<str:nid>/', views.editEmailNotification, name="edit-email-notification"),
    path('team/<str:pk>/settings/notifications/<str:nid>/delete/', views.deleteEmailNotification, name="delete-email-notification"),
    path('team/<str:pk>/settings/links/', views.allTeamLinks, name="team-notification-links"),
    path('team/<str:pk>/settings/links/add/', views.createTeamLink, name="create-notification-link"),
    path('team/<str:pk>/settings/links/<str:lid>/', views.editTeamLink, name="edit-notification-link"),
    path('team/<str:pk>/settings/links/<str:lid>/delete/', views.deleteTeamLink, name="delete-notification-link"),
    path('team/<str:pk>/delete-team/', views.deleteTeam, name="delete-team"),

    #  team members
    path('team/<str:pk>/invite-to-team/', views.invite_to_team, name="invite-to-team"),
    path('team/<str:pk>/invite-athlete-signup/', views.inviteAthleteToSignUp, name="invite-athlete-signup"),
    path('team/<str:pk>/members/', views.teamMembers, name="team-members"),
    path('team/<str:pk>/members/edit/', views.editTeamMembers, name="team-members-edit"),
    path('team/<str:pk>/remove-member/<str:memberid>', views.removeFromTeam, name="remove-member"),
    
    # team schedule
    path('team/<str:pk>/schedule/', views.teamScheduleAll, name="team-schedule"), # view calendar
    path('team/<str:pk>/schedule/add-event/', views.createTeamEvent, name="create-event"), # create new event to calendar
    path('team/<str:pk>/schedule/<str:eid>/', views.viewTeamEvent, name="team-event"), # view event and attendance
    path('team/<str:pk>/schedule/<str:eid>/edit/', views.editTeamEvent, name="edit-teamevent"), # edit team evemt only
    path('team/<str:pk>/schedule/<str:eid>/delete/', views.deleteTeamEvent, name="delete-teamevent"), # delete team event

    # team schedule attendance
    path('team/<str:pk>/schedule/<str:eventid>/attendance/', views.TeamEventAttendance, name="attendance"), # edit attendance
    path('team/<str:pk>/schedule/<str:eventid>/attendance/add/', views.addTeamMemberToEvent, name="add-attendance"), # add team member to event
    path('team/<str:pk>/schedule/<str:eventid>/remove-attendance/<str:attendanceid>/', views.removeTeamMemberFromEvent, name="remove-attendance"), # remove team member from event

    # team Physical-assessments
    path('team/<str:pk>/physical-assessments/', views.allTeamPhysicalAssessment, name="physical-assessments"), # all PA
    path('team/<str:pk>/physical-assessments/create/', views.createPhysicalAssessment, name="create-physical-assessments"), # creat new PA
    path('team/<str:pk>/physical-assessments/<str:papk>/', views.singlePhysicalAssessment, name="single-physical-assessment"), # view single PA with measurements
    # path('team/<str:pk>/physical-assessments/<str:papk>/edit/', views.editSinglePhysicalAssessment, name="edit-single-physical-assessment"),
    path('team/<str:pk>/physical-assessments/<str:papk>/download-physical-assessment-csv/', views.downloadPhysicalAssessmentScore, name="download_physical_assessment_score"),
    path('team/<str:pk>/physical-assessments/<str:papk>/delete/', views.deletePhysicalAssessment, name="delete-single-physical-assessment"), #delete physicalassesment
    

    # team Physical-assessment measurement records

    path('team/<str:pk>/physical-assessments/<str:papk>/new/', views.newPhysicalAssessmentMeasurement, name="physical-assessment-new-measurement"), # create PA measurement date with empty scores for team members
    path('team/<str:pk>/physical-assessments/<str:papk>/edit/<str:recordid>/', views.editPhysicalAssessmentMeasurement, name="edit-physical-assessment-measurement"), # edit PA measurement for team members
    path('team/<str:pk>/physical-assessments/<str:papk>/delete/<str:recordid>/', views.deletePhysicalAssessmentMeasurements, name="delete-physical-assessment-measurement"), # delete measuremenets for date
    path('team/<str:pk>/physical-assessments/<str:papk>/add/<str:recordid>/team-member/', views.addTeamMemberToPhysicalAssessmentMeasurement, name="add-team-member-physical-assessment-score"), # add team member to PA record score
    path('team/<str:pk>/physical-assessments/<str:papk>/delete/<str:recordid>/teammember/<str:memberid>/', views.deleteTeamMemberPhysicalAssessmentMeasurement, name="delete-team-member-measurement"), # delete measuremenet for single team member

    # Org team  Physical-assessment
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/', views.organizationSinglePhysicalAssessment, name="org-single-physical-assessment"), # view single team Org PA with measurements
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/download-physical-assessment-csv/', views.downloadOrganizationPhysicalAssessmentScore, name="download_org_physical_assessment_score"),
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/new/', views.organizationNewPhysicalAssessmentMeasurement, name="org-physical-assessment-new-measurement"), # create org new date record
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/edit/<str:recordid>/', views.organizationEditPhysicalAssessmentMeasurement, name="edit-org-physical-assessment-measurement"), # edit org PA measurement for team members
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/delete/<str:recordid>/', views.organizationDeletePhysicalAssessmentMeasurements, name="org-delete-physical-assessment-measurement"), # delete measuremenets for date
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/add/<str:recordid>/team-member/', views.organizationAddTeamMemberToPhysicalAssessmentMeasurement, name="org-add-team-member-physical-assessment-score"), # add team member to PA record score
    path('team/<str:pk>/physical-assessments/organization/<str:opaid>/delete/<str:recordid>/teammember/<str:memberid>/', views.organizationDeleteTeamMemberPhysicalAssessmentMeasurement, name="org-delete-team-member-measurement"), # delete measuremenet for single team member
    
    # team analytics
    path('team/<str:pk>/analytics/', views.teamAnalytics, name="team-analytics"),
    path('team/<str:pk>/analytics/seasons/', views.viewTeamSeasons, name="team-seasons"),
    path('team/<str:pk>/analytics/seasons/create/', views.createTeamSeason, name="create-team-season"),
    path('team/<str:pk>/analytics/seasons/edit/<str:sid>/', views.editTeamSeason, name="edit-team-season"),
    path('team/<str:pk>/analytics/seasons/delete/<str:sid>/', views.deleteTeamSeason, name="delete-team-season"),
    path('team/<str:pk>/analytics/<str:mpk>/', views.teamMemberAnalytics, name="team-member-analytics"),


    # teamplaybook
    path('team/<str:pk>/playbook/', views.viewTactics, name="view-playbook"),
    path('team/<str:pk>/playbook/add/', views.add_team_tactic, name="add-tactic"),
    path('team/<str:pk>/playbook/draw/', views.drawNewTactic, name="draw-playbook"),
    path('team/<str:pk>/playbook/<str:tid>/', views.viewSingleTactic, name="view-tactic"),
    path('team/<str:pk>/playbook/<str:tid>/edit/', views.editTactic, name="edit-tactic"),
    path('team/<str:pk>/playbook/<str:tid>/edit-tactic-plays/', views.editTacticPlays, name="edit-tactic-plays"),
    path('team/<str:pk>/playbook/<str:tid>/delete/', views.deleteTactic, name="delete-team-tactic"),
    path('team/<str:pk>/playbook/<str:tid>/upload_tactic_play/', views.upload_tactic_play, name="upload_tactic_play"),
    path('team/<str:pk>/playbook/<str:tid>/delete_play/<str:pid>/', views.deleteTacticPlay, name="delete-tactic-play"),

    # leave team

    path('team/<str:pk>/leave/', views.leaveTeam, name='leave-team'),

  
    
]