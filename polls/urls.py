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

    path("admin_users/", views.adm_users, name="adm_users"),
    path("admin_load_users/", views.adm_load_users, name="adm_load_users"),
    path("admin_profile/", views.adm_user_profile, name="adm_create_user"),
    path("admin_rofile/<int:usr_id>", views.adm_user_profile, name="adm_user_profile"),
    path("change_password/", views.change_password, name="change_password"),
    path("admin_delete_user/<int:usr_id>", views.adm_delete_user, name="adm_delete_user"),

    path("admin_events/", views.adm_events, name="adm_events"),
    path("admin_create_event/", views.adm_event_detail, name="adm_create_event"),
    path("admin_update_event/<int:evt_id>/", views.adm_event_detail, name="adm_event_detail"),
    path("admin_adm_delete_event/<int:evt_id>", views.adm_delete_event, name="adm_delete_event"),

    path("admin_groups/", views.adm_groups, name="adm_groups"),
    path("admin_create_group/", views.adm_group_detail, name="adm_group_detail"),
    path("admin_update_group/<int:grp_id>/", views.adm_group_detail, name="adm_group_detail"),
    path("admin_adm_delete_group/<int:grp_id>", views.adm_delete_group, name="adm_delete_group"),

    path("admin_options/", views.adm_options, name="adm_options"),

    path("<slug:comp_slug>/", views.company_home, name="company_home"),

    path("<slug:comp_slug>/<slug:event_slug>/", views.event, name="event"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>", views.question, name="question"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>/vote", views.vote, name="vote"),
    path("<slug:comp_slug>/<slug:event_slug>/results", views.results, name="results"),
]
