# -*-coding:Utf-8 -*

from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.index, name="index"),
    path("get_chart_data/", views.get_chart_data, name="chart_data"),
    path("set_proxy/", views.set_proxy, name="set_proxy"),
    path("accept_proxy/", views.accept_proxy, name="accept_proxy"),
    path("cancel_proxy/", views.cancel_proxy, name="cancel_proxy"),
    path("sign_up/", views.new_user, name="sign_up"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),

    path("admin_users/", views.admin_users, name="admin_users"),
    path("load_users/", views.load_users, name="load_users"),
    path("profile/", views.user_profile, name="create_user"),
    path("profile/<int:usr_id>", views.user_profile, name="user_profile"),
    path("change_password/", views.change_password, name="change_password"),
    path("delete_user/<int:usr_id>", views.delete_user, name="delete_user"),

    path("admin_events/", views.admin_events, name="admin_events"),
    path("admin_groups/", views.admin_groups, name="admin_groups"),

    path("<slug:comp_slug>/", views.company_home, name="company_home"),

    path("<slug:comp_slug>/<slug:event_slug>/", views.event, name="event"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>", views.question, name="question"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>/vote", views.vote, name="vote"),
    path("<slug:comp_slug>/<slug:event_slug>/results", views.results, name="results"),
]
