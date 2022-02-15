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

    path("<slug:comp_slug>/", views.company_home, name="company_home"),

    path("<slug:comp_slug>/admin_users/", views.adm_users, name="adm_users"),
    path("<slug:comp_slug>/admin_load_users/", views.adm_load_users, name="adm_load_users"),
    path("<slug:comp_slug>/admin_profile/", views.adm_user_profile, name="adm_create_user"),
    path("<slug:comp_slug>/admin_profile/<int:usr_id>", views.adm_user_profile, name="adm_user_profile"),
    path("<slug:comp_slug>/change_password/", views.change_password, name="change_password"),
    path("<slug:comp_slug>/admin_delete_user/<int:usr_id>", views.adm_delete_user, name="adm_delete_user"),

    path("<slug:comp_slug>/admin_events/", views.adm_events, name="adm_events"),
    path("<slug:comp_slug>/admin_create_event/", views.adm_event_detail, name="adm_create_event"),
    path("<slug:comp_slug>/admin_update_event/<int:evt_id>/", views.adm_event_detail, name="adm_event_detail"),
    path("<slug:comp_slug>/admin_delete_event/<int:evt_id>", views.adm_delete_event, name="adm_delete_event"),

    path("<slug:comp_slug>/admin_groups/", views.adm_groups, name="adm_groups"),
    path("<slug:comp_slug>/admin_group_detail/", views.adm_group_detail, name="adm_create_group"),
    path("<slug:comp_slug>/admin_group_detail/<int:grp_id>/", views.adm_group_detail, name="adm_group_detail"),
    path("<slug:comp_slug>/admin_delete_group/<int:grp_id>", views.adm_delete_group, name="adm_delete_group"),

    path("<slug:comp_slug>/admin_options/", views.adm_options, name="adm_options"),
    path("<slug:comp_slug>/admin_update_options/", views.adm_update_options, name="adm_update_options"),

    path("<slug:comp_slug>/<slug:event_slug>/", views.event, name="event"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>", views.question, name="question"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>/vote", views.vote, name="vote"),
    path("<slug:comp_slug>/<slug:event_slug>/results", views.results, name="results"),
]
