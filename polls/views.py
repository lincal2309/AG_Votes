# -*-coding:Utf-8 -*

from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_list_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings

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
    """ Home page """

    company = Company.get_company(1)
    next_event_list = Event.get_next_events(company)
    return render(request, 'polls/index.html', locals())


@login_required
def event(request, event_slug):
    """ Event details page page """

    # Define event context
    event = Event.get_event(event_slug)
    question_list = Question.get_question_list(event_slug)
    nb_questions = len(question_list)

    # Check if connected user is part of the event and is authorized to vote
    user_can_vote = False
    if request.user.is_staff or EventGroup.user_in_event_group(event_slug, request.user):
        user_can_vote = True

    return render(request, 'polls/event.html', locals())

def get_chart_data(request):
    """ Gather and send information to build charts via ajax get request """

    # List of colors
    background_colors = [
        'rgba(124, 252, 0, 0.2)',
        'rgba(255, 99, 132, 0.2)',
        'rgba(255, 159, 64, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(128, 128, 128, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(222, 184, 135, 0.2)',
        'rgba(127, 255, 212, 0.2)'
    ]
    border_colors = [
        'rgba(124, 252, 0, 1)',
        'rgba(255, 99, 132, 1)',
        'rgba(255, 159, 64, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(128, 128, 128, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(222, 184, 135, 1)',
        'rgba(127, 255, 212, 1)'
    ]

    event_slug = request.GET['event_slug']
    question_no = int(request.GET['question_no'])

    choice_list = Choice.get_choice_list(event_slug, question_no).values('choice_text', 'votes')
    total_votes = EventGroup.count_total_votes(event_slug)

    labels = [choice['choice_text'] for choice in choice_list]
    values = [choice['votes'] for choice in choice_list]
    nb_votes = sum(values)

    chart_background_colors = background_colors
    chart_border_colors = border_colors

    while len(chart_background_colors) < nb_votes:
        chart_background_colors += background_colors
        chart_border_colors += border_colors

    data = {
        'nb_votes': nb_votes,
        'total_votes': total_votes,
        'labels': labels,
        'values': values,
        'backgroundColor': chart_background_colors,
        'borderColor': chart_border_colors,
        }

    return JsonResponse(data)


@login_required
def question(request, event_slug, question_no):
    """ Questions details page 
        Manage information display """

    # Necessary info for the template
    event = Event.get_event(event_slug)
    question = Question.get_question(event_slug, question_no)
    choice_list = Choice.get_choice_list(event_slug, question_no)
    last_question = False

    # Start event - staff only used "Launch event" button
    if request.user.is_staff and not event.current:
        event.set_current()

        # Initialize users vote table - includes proxyholders
        UserVote.init_uservotes(event_slug)

    # Gather user's info about the current question
    if not request.user.is_staff:
        user_vote = UserVote.get_user_vote(request.user, question_no)

    # Check if current question is the last one
    if question_no == len(Question.get_question_list(event_slug)):
        last_question = True

    return render(request, 'polls/question.html', locals())
        

def vote(request, event_slug, question_no):
    """ Manage users' votes """

    choice_id = request.POST['choice']

    # Register user's vote
    Choice.add_vote(choice_id)
    # Update user and set has_voted = True
    user_vote = UserVote.set_vote(request.user, question_no)

    data = {'success': 'OK', 'voted': user_vote.has_voted}

    return JsonResponse(data)



@login_required
def results(request, event_slug):
    """ Results page """

    event = Event.get_event(event_slug)
    return render(request, 'polls/results.html', locals())

