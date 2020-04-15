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
    # path("<slug:comp_slug>/create_user/", views.create_user, name="create_user"),
    path("<slug:comp_slug>/update_user/<int:pk>", views.update_user, name="update_user"),
    path("update_user/<int:pk>", views.UpdateUserView.as_view(), name="updt_user"),
    path("delete_user/<int:pk>", views.DeleteUserView.as_view(), name="delete_user"),
    path("<slug:comp_slug>/", views.company_home, name="company_home"),
    path("<slug:comp_slug>/administration/<int:admin_id>", views.admin_polls, name="admin_polls"),
    path("<slug:comp_slug>/<slug:event_slug>/", views.event, name="event"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>", views.question, name="question"),
    path("<slug:comp_slug>/<slug:event_slug>/<int:question_no>/vote", views.vote, name="vote"),
    path("<slug:comp_slug>/<slug:event_slug>/results", views.results, name="results"),
]
