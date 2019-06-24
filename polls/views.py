# -*-coding:Utf-8 -*

from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.conf import settings

import json

from .models import Company, Event, Question, Choice, UserVote, EventGroup,\
    Result, Procuration
from .forms import UserForm
from .pollsmail import PollsMail

debug = settings.DEBUG
background_colors = settings.BACKGROUND_COLORS
border_colors = settings.BORDER_COLORS


# =======================
#    Global functions
# =======================

def init_event(event):
    UserVote.init_uservotes(event)
    event.set_current()

def set_chart_data(event, evt_group_list, question_no):

    # Initialize charts variables
    group_data = {}
    nb_groups = 0

    # Initialize global results data
    global_choice_list = Choice.get_choice_list(event.slug).values('choice_text')
    group_vote = {}
    global_total_votes = 0
    global_nb_votes = 0
    for choice in global_choice_list:
        group_vote[choice['choice_text']] = 0

    # Gather votes info for each group
    for evt_group in evt_group_list:
        nb_groups += 1
        total_votes = EventGroup.objects.filter(id=evt_group.id).\
            aggregate(Count('users'))['users__count']

        choice_list = Result.get_vote_list(evt_group, question_no).\
            values('choice__choice_text', 'votes', 'group_weight')

        labels = [choice['choice__choice_text'] for choice in choice_list]
        values = [choice['votes'] for choice in choice_list]
        nb_votes = sum(values)

        chart_nb = "chart" + str(nb_groups)
        group_data[chart_nb] = {
            'nb_votes': nb_votes,
            'total_votes': total_votes,
            'labels': labels,
            'values': values,
            }

        # Calculate aggregate results
        # Use if / elif to ease adding future rules
        global_total_votes += total_votes
        global_nb_votes += nb_votes
        weight = choice_list[0]['group_weight']
        if event.rule == 'MAJ':
            # A MODIFIER : cas d'égalité, pas de valeur... (règles à définir)
            max_val = values.index(max(values))
            group_vote[labels[max_val]] += weight
        elif event.rule == 'PROP':
            # Calculate totals per choice, including group's weight
            # Addition of each group's result
            for i, choice in enumerate(labels):
                group_vote[choice] += values[i] * weight / 100

    if event.rule == 'PROP':
        # Calculate percentage for each choice
        total_votes = 0
        for val in group_vote.values():
            total_votes += val
        # Calculate global results only if at least 1 vote
        if total_votes > 0:
            for choice, value in group_vote.items():
                group_vote[choice] = round((value / total_votes) * 100, 2)

    # Setup global info for charts
    global_labels = []
    global_values = []
    for label, value in group_vote.items():
        global_labels.append(label)
        global_values.append(value)

    group_data['global'] = {
        'nb_votes': global_nb_votes,
        'total_votes': global_total_votes,
        'labels': global_labels,
        'values': global_values,
        }

    chart_background_colors = background_colors
    chart_border_colors = border_colors

    # Extends color lists to fit with nb values to display
    while len(chart_background_colors) < nb_votes:
        chart_background_colors += background_colors
        chart_border_colors += border_colors

    data = {
        'chart_data': group_data,
        'nb_charts': nb_groups,
        'backgroundColor': chart_background_colors,
        'borderColor': chart_border_colors,
        }

    return data


# =======================
#  User management views
# =======================

@user_passes_test(lambda u: u.is_superuser)
def create_user(request):
    # ================================================
    # For development purposes only - superuser only
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


# =======================
#     Template views
# =======================

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
    if EventGroup.user_in_event(event_slug, request.user):
        user_can_vote = True

        # Get user's proxy status
        proxy_list, user_proxy, user_proxy_list =\
            Procuration.get_proxy_status(event_slug, request.user)

    return render(request, 'polls/event.html', locals())


@login_required
def question(request, event_slug, question_no):
    """ Questions details page 
        Manage information display """

    # Necessary info for the template
    event = Event.get_event(event_slug)
    evt_group_list = EventGroup.get_list(event_slug)
    question = Question.get_question(event_slug, question_no)
    choice_list = Choice.get_choice_list(event_slug)
    last_question = False

    # Start event - occur when staff only used "Launch event" button
    if request.user.is_staff and not event.current:
        # Event can be launched only if total groups' weight == 100
        if EventGroup.objects.filter(event=event).\
                aggregate(Sum('weight'))['weight__sum'] != 100:
            return redirect('polls:event', event_slug=event_slug)
        else:
            # Initialize users vote & results table
            init_event(event)

    # Gather user's info about the current question
    if not request.user.is_staff:
        user_vote = UserVote.get_user_vote(event_slug, request.user,
            question_no)

    # Check if current question is the last one
    if question_no == len(Question.get_question_list(event_slug)):
        last_question = True

    return render(request, 'polls/question.html', locals())


@login_required
def results(request, event_slug):
    """ Results page """

    event = Event.get_event(event_slug)
    question_list = Question.get_question_list(event_slug)
    nb_questions = len(question_list)

    return render(request, 'polls/results.html', locals())


# =======================
#      Action views
# =======================

def get_chart_data(request):
    """ Gather and send information to build charts via ajax get request """

    event_slug = request.GET['event_slug']
    question_no = int(request.GET['question_no'])

    event = Event.get_event(event_slug)
    evt_group_list = EventGroup.get_list(event_slug)

    data = set_chart_data(event, evt_group_list, question_no)

    return JsonResponse(data)

def vote(request, event_slug, question_no):
    """ Manage users' votes """

    choice_id = request.POST['choice']
    user_vote = UserVote.set_vote(event_slug, request.user, question_no,
        choice_id)

    data = {'success': 'OK', 'nb_votes': user_vote.nb_user_votes}

    return JsonResponse(data)

def set_proxy(request):
    """ Set proxyholder """

    user = User.objects.get(id=request.POST['user'])
    proxy = User.objects.get(id=request.POST['proxy'])
    event = Event.get_event(request.POST['event_slug'])

    Procuration.set_user_proxy(event, user, proxy)
    PollsMail('ask_proxy', event, sender=[user.email],
        recipient_list=[proxy.email], user=user, proxy=proxy)

    data = {'proxy_f_name': proxy.first_name, 'proxy_l_name': proxy.last_name,
        'proxy': request.POST['proxy']}

    return JsonResponse(data)

def accept_proxy(request):
    """ Accept proxy request """

    user = User.objects.get(id=request.POST['user'])
    # decode list sent in JSON format
    proxy_list = json.loads(request.POST['cancel_list'])

    event = Event.get_event(request.POST['event_slug'])

    for proxy_id in proxy_list:
        Procuration.confirm_proxy(event, user, int(proxy_id))
        PollsMail('confirm_proxy', event, sender=[user.email],
            user=user, proxy_id=proxy_id)

    data = {'status': 'Success'}

    return JsonResponse(data)

def cancel_proxy(request):
    """ Cancel or refuse proxy """

    event_slug = request.POST['event']

    if request.POST['Action'] == 'Refuse':
        proxy_list = request.POST.getlist('user_proxy')
        for proxy in proxy_list:
            Procuration.cancel_proxy(event_slug, int(proxy), request.user)
    else:
        Procuration.cancel_proxy(event_slug, request.user)

    return redirect('polls:event', event_slug=event_slug)
