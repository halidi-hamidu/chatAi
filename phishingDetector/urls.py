from django.urls import path
from .import views

app_name = "phishingDetector"

urlpatterns = [
    path('', views.homeView, name="homeView"),
    path('chats', views.chatsView, name="chatsView"),
    path('messages', views.messagesView, name="messagesView"),
    path("settings/", views.settingsView, name="settingsView"),
    path("settings/update/user/<int:user_id>/", views.settingsUpdateView, name="settingsUpdateView"),
    path("settings/delete/user/<int:user_id>/", views.settingsDeleteView, name="settingsDeleteView"),
    path("settings/authorization/user/<int:user_id>/", views.userAuthorizationView, name="userAuthorizationView"),
]