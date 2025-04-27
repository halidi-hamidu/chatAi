from django.urls import path
from . import views

app_name = "authentication"
urlpatterns = [
    path("", views.loginView, name="loginView"),
    path("register/", views.registerView, name="registerView"),
    path("logout/", views.logoutView, name="logoutView"),
    path("users/", views.get_user, name="get_user"),
]