# -*-coding:Utf-8 -*

from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path('', views.index, name='index'),
    path('sign_up/', views.create_user, name='sign_up'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('reinit/', views.reinit, name='reinit'),
    path('<slug:event_slug>/', views.event, name='event'),
    path('<slug:event_slug>/<int:question_no>', views.question, name='question'),
    path('<slug:event_slug>/results', views.results, name='results'),

]