from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.loginUser, name="login"),
    path("logout/", views.logoutUser, name="logout"),
    path("register/<uuid:token>/", views.registerAthlete, name="register"),
    path('register-coach/<uuid:token>/', views.registerCoach, name="register-coach"),
    path('', views.landing, name="home"),
    # path('profile/<str:pk>/', views.userProfile, name="user-profile"),
    path('account/', views.userAccount, name="account"),
    path('account/edit/', views.editAccount, name="edit-account"),
    path('account/delete/', views.deleteUserAccount, name="delete-account"),
    path('accept-invite/<uuid:token>/', views.accept_invitation, name='accept-invitation'),
    path('accept-org-invite/<uuid:token>/', views.acceptOrgInvitation, name='accept-org-invitation'),

]
