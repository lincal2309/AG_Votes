# -*-coding:Utf-8 -*

from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path('', views.index, name='index'),
    path('get_chart_data/', views.get_chart_data, name='chart_data'),
    path('set_proxy/', views.set_proxy, name='set_proxy'),
    path('accept_proxy/', views.accept_proxy, name='accept_proxy'),
    path('cancel_proxy/', views.cancel_proxy, name='cancel_proxy'),
    path('sign_up/', views.create_user, name='sign_up'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('<slug:event_slug>/', views.event, name='event'),
    path('<slug:event_slug>/<int:question_no>', views.question,
         name='question'),
    path('<slug:event_slug>/<int:question_no>/vote', views.vote,
         name='vote'),
    path('<slug:event_slug>/results', views.results, name='results'),
]
