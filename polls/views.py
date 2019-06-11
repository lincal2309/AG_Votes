# -*-coding:Utf-8 -*

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, reverse, get_list_or_404
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.files.storage import FileSystemStorage
from django.template.loader import render_to_string
import json

from weasyprint import HTML


from .models import Company, Event, Question, Choice, UserVote, EventGroup, Result, Procuration
from .forms import UserForm
from .utils import PollsMail

debug = settings.DEBUG


# Global functions
def init_event(event):
    UserVote.init_uservotes(event)
    event.set_current()

    
# =======================
#  User management views
# =======================

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
                # return redirect(reverse('polls:index'))
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

    Procuration.objects.filter(event=event).delete()
    question_list = get_list_or_404(Question, event=event)


    # Resets users vote status
    for question in question_list:
        UserVote.objects.filter(question=question).delete()
        Result.objects.filter(question=question).delete()

    # Reinitialize complete view
    nb_questions = len(question_list)

    user_can_vote = False
    if EventGroup.user_in_event(event.slug, request.user):
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
        proxy_list, user_proxy, user_proxy_list = Procuration.get_proxy_status(event_slug, request.user)

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
        # Initialize users vote & results table
        init_event(event)

    # Gather user's info about the current question
    if not request.user.is_staff:
        user_vote = UserVote.get_user_vote(event_slug, request.user, question_no)

    # Check if current question is the last one
    if question_no == len(Question.get_question_list(event_slug)):
        last_question = True

    return render(request, 'polls/question.html', locals())
        

@login_required
def results(request, event_slug):
    """ Results page """

    event = Event.get_event(event_slug)
    return render(request, 'polls/results.html', locals())



# =======================
#      Action views
# =======================

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

    event = Event.get_event(event_slug)
    evt_group_list = EventGroup.get_list(event_slug)

    # Initialize charts variables
    group_data = {}
    nb_groups = 0

    # Initialize global results data
    global_choice_list = Choice.get_choice_list(event_slug).values('choice_text', 'votes')
    group_vote = {}
    global_total_votes = 0
    global_nb_votes = 0
    for choice in global_choice_list:
        group_vote[choice['choice_text']] = 0

    # Gather votes info for each group
    for evt_group in evt_group_list:
        nb_groups += 1
        total_votes = EventGroup.objects.filter(id=evt_group.id).aggregate(Count('users'))['users__count']
    
        choice_list = Result.get_vote_list(evt_group, question_no).values('choice__choice_text', 'votes', 'group_weight')

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
            max_val = values.index(max(values))
            group_vote[labels[max_val]] += weight
        elif event.rule == 'PROP':
            for i, choice in enumerate(labels):
                group_vote[choice] += values[i] * weight / 100

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

    return JsonResponse(data)


def vote(request, event_slug, question_no):
    """ Manage users' votes """

    choice_id = request.POST['choice']
    user_vote = UserVote.set_vote(event_slug, request.user, question_no, choice_id)

    data = {'success': 'OK', 'nb_votes': user_vote.nb_user_votes}

    return JsonResponse(data)


def set_proxy(request):
    """ Set proxyholder """

    user = User.objects.get(id=request.POST['user'])
    proxy = User.objects.get(id=request.POST['proxy'])
    event = Event.get_event(request.POST['event_slug'])

    Procuration.set_user_proxy(event, user, proxy)
    PollsMail('ask_proxy', event, sender=[user.email], recipient_list=[proxy.email], user=user, proxy=proxy)

    data = {'proxy_f_name': proxy.first_name, 'proxy_l_name': proxy.last_name, 'proxy': request.POST['proxy']}

    return JsonResponse(data)

def accept_proxy(request):
    """ Accept proxy request """

    user = User.objects.get(id=request.POST['user'])
    proxy_list = json.loads(request.POST['cancel_list'])   # decode list sent in JSON format
    event = Event.get_event(request.POST['event_slug'])

    for proxy_id in proxy_list:
        Procuration.confirm_proxy(event, user, int(proxy_id))
        PollsMail('confirm_proxy', event, sender=[user.email], user=user, proxy_id=proxy_id)

    data = {'status': 'Success'}

    return JsonResponse(data)

def cancel_proxy(request):

    event_slug = request.POST['event']

    if request.POST['Action'] == 'Refuse':
        proxy_list = request.POST.getlist('user_proxy')
        for proxy in proxy_list:
            Procuration.cancel_proxy(event_slug, int(proxy), request.user)
    else:
        Procuration.cancel_proxy(event_slug, request.user)


    return redirect('polls:event', event_slug=event_slug)


def invite_users(request):
    event_slug = request.POST['event_to_reinit']
    event = Event.get_event(event_slug)
    company = Company.objects.get(event=event)
    question_list = Question.get_question_list(event_slug)
    context_data = {'company': company, 'event': event, 'question_list': question_list}


