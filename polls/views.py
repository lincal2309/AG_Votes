# -*-coding:Utf-8 -*

from django.shortcuts import render, redirect, reverse, get_list_or_404, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings

import dash
import dash_core_components as dcc
import dash_html_components as html

from django_plotly_dash import DjangoDash

from .models import Company, Event, Question, Choice, UserVote, EventGroup
from .forms import UserForm

debug = settings.DEBUG

#  User management views
def create_user(request):
    # ================================================
    # For development purposes only
    # ================================================
    error = False

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            if User.objects.filter(username=username):
                user_exists = True
            else:
                User.objects.create_user(username=username, 
                    password=password)
                user = authenticate(username=username, password=password)
                login(request, user)
                return redirect(reverse('polls:index'))
    else:
        form = UserForm()

    return render(request, 'polls/sign_up.html', locals())


def login_user(request):
    error = False

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect(reverse('polls:index'))
            else:
                error = True
    else:
        form = UserForm()

    return render(request, 'polls/login.html', locals())


def logout_user(request):
    logout(request)
    return redirect(reverse('polls:index'))



@login_required
def index(request):
    company = Company.objects.get(id=1)
    next_event_list = get_list_or_404(Event, company=company, event_date__gte=timezone.now())
    return render(request, 'polls/index.html', locals())


@login_required
def event(request, event_slug):
    # Define event context
    event = get_object_or_404(Event, slug=event_slug)
    question_list = get_list_or_404(Question, event=event)
    nb_questions = len(question_list)

    # Check if connected user is part of the event and is authorized to vote
    user_can_vote = False
    if request.user.is_staff or len(EventGroup.objects.filter(event=event, user=request.user)) > 0:
        user_can_vote = True

    # Development only : initialize event at each page display to ease tests
    # if debug and request.user.is_staff:
    #     event.current = False
    #     event.save()
    #     question_list = get_list_or_404(Question, event=event)
    #     for question in question_list:
    #         UserVote.objects.filter(question=question).delete()

    return render(request, 'polls/event.html', locals())

def reinit(request):
    # ==========================================================================
    # DEVELOPMENT ONLY : allows to set event to "not started" for tests purposes
    # Should be removed before pushing to production
    # ==========================================================================
    event = Event.objects.get(slug=request.POST['event_to_reinit'])

    # Set event to "not started"
    event.current = False
    event.save()

    question_list = get_list_or_404(Question, event=event)

    # Resets users vote status
    for question in question_list:
        UserVote.objects.filter(question=question).delete()
        for choice in get_list_or_404(Choice, question=question):
            choice.votes = 0
            choice.save()

    # Reinitialize complete view
    nb_questions = len(question_list)

    user_can_vote = False
    if request.user.is_staff or len(get_list_or_404(EventGroup, event=event, user=request.user)) > 0:
        user_can_vote = True

    return render(request, 'polls/event.html', locals())


@login_required
def question(request, event_slug, question_no):
    event = get_object_or_404(Event, slug=event_slug)
    last_question = False

    # Start event - staff only
    if not event.current:
        event.current = True
        event.save()

        # Initialize users votge table - includes proxyholders
        event_user_list = get_list_or_404(EventGroup, event=event)
        for event_user in event_user_list:
            question_list = get_list_or_404(Question, event=event)
            for question in question_list:
                UserVote.objects.create(user=event_user.user, question=question)


    if request.method == 'POST':
        # Occurs when a user sends a vote
        question = get_list_or_404(Question, event=event)[question_no - 1]
        choice = get_object_or_404(Choice, id=request.POST['choice'])
        choice.votes += 1
        choice.save()
        user_vote = get_object_or_404(UserVote, question=question, user=request.user)    # A modifier pour la gestion des pouvoirs
        user_vote.as_voted = True
        user_vote.save()
        if question_no == len(get_list_or_404(Question, event=event)):
            last_question = True
    else:
        question = get_list_or_404(Question, event=event)[question_no]
        if not request.user.is_staff:
            user_vote = UserVote.objects.get(user=request.user, question=question)
        question_no += 1

    if question_no == len(get_list_or_404(Question, event=event)):
        last_question = True
    choice_list = get_list_or_404(Choice, question=question)
    nb_choices = len(choice_list)

    total_votes = Choice.objects.filter(question=question).aggregate(Sum('votes'))['votes__sum']
    result_list = {}
    for choice in choice_list:
        if total_votes > 0:
            nb_votes = (choice.votes / total_votes) * 100
        else:
            nb_votes = 0
        result_list[choice.choice_text] = nb_votes


    # =================================================
    # 
    # TEST ON CHARTS
    # 
    # =================================================

    if debug:
        app = DjangoDash('SimpleExample', serve_locally=True)
    else:
        app = DjangoDash('SimpleExample')

    app.layout = html.Div([
        dcc.RadioItems(
            id='dropdown-color',
            options=[{'label': c, 'value': c.lower()} for c in ['Red', 'Green', 'Blue']],
            value='red'
        ),
        html.Div(id='output-color'),
        dcc.RadioItems(
            id='dropdown-size',
            options=[{'label': i,
                    'value': j} for i, j in [('L','large'), ('M','medium'), ('S','small')]],
            value='medium'
        ),
        html.Div(id='output-size')

    ])

    @app.callback(
        dash.dependencies.Output('output-color', 'children'),
        [dash.dependencies.Input('dropdown-color', 'value')])
    def callback_color(dropdown_value):
        return "The selected color is %s." % dropdown_value

    @app.callback(
        dash.dependencies.Output('output-size', 'children'),
        [dash.dependencies.Input('dropdown-color', 'value'),
        dash.dependencies.Input('dropdown-size', 'value')])
    def callback_size(dropdown_color, dropdown_size):
        return "The chosen T-shirt is a %s %s one." %(dropdown_size,
                                                    dropdown_color)


    # =================================================


    return render(request, 'polls/question.html', locals())
        

@login_required
def results(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    return render(request, 'polls/results.html', locals())

