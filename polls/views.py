# -*-coding:Utf-8 -*

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, reverse
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .forms import UserBaseForm, UserCompForm

import json

from .models import (
    Company,
    Event,
    Question,
    Choice,
    UserVote,
    EventGroup,
    Result,
    Procuration,
    UserComp,
)
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
    global_choice_list = Choice.get_choice_list(event.slug).values("choice_text")
    group_vote = {}
    global_total_votes = 0
    global_nb_votes = 0
    for choice in global_choice_list:
        group_vote[choice["choice_text"]] = 0

    # Gather votes info for each group
    for evt_group in evt_group_list:
        nb_groups += 1
        total_votes = EventGroup.objects.filter(id=evt_group.id).aggregate(
            Count("users")
        )["users__count"]

        result_list = Result.get_vote_list(event, evt_group, question_no).values(
            "choice__choice_text", "votes", "group_weight"
        )

        labels = [choice["choice__choice_text"] for choice in result_list]
        values = [choice["votes"] for choice in result_list]
        nb_votes = sum(values)

        chart_nb = "chart" + str(nb_groups)
        group_data[chart_nb] = {
            "nb_votes": nb_votes,
            "total_votes": total_votes,
            "labels": labels,
            "values": values,
        }

        # Calculate aggregate results
        # Use if / elif to ease adding future rules
        global_total_votes += total_votes
        global_nb_votes += nb_votes
        weight = result_list[0]["group_weight"]
        if event.rule == "MAJ":
            # A MODIFIER : cas d'égalité, pas de valeur... (règles à définir)
            max_val = values.index(max(values))
            group_vote[labels[max_val]] += weight
        elif event.rule == "PROP":
            # Calculate totals per choice, including group's weight
            # Addition of each group's result
            for i, choice in enumerate(labels):
                if choice in group_vote:
                    group_vote[choice] += values[i] * weight / 100

    if event.rule == "PROP":
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

    group_data["global"] = {
        "nb_votes": global_nb_votes,
        "total_votes": global_total_votes,
        "labels": global_labels,
        "values": global_values,
    }

    chart_background_colors = background_colors
    chart_border_colors = border_colors

    # Extends color lists to fit with nb values to display
    while len(chart_background_colors) < nb_votes:
        chart_background_colors += background_colors
        chart_border_colors += border_colors

    data = {
        "chart_data": group_data,
        "nb_charts": nb_groups,
        "backgroundColor": chart_background_colors,
        "borderColor": chart_border_colors,
    }

    return data


# =======================
#  User management views
# =======================


@user_passes_test(lambda u: u.is_superuser)
def new_user(request):
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
                User.objects.create_user(username=username, password=password)
    else:
        form = UserForm()

    return render(request, "polls/sign_up.html", locals())


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
                return redirect(reverse("polls:index"))
            else:
                error = True
    else:
        form = UserForm()

    return render(request, "polls/login.html", locals())


def logout_user(request):
    logout(request)
    return redirect(reverse("polls:index"))


# =======================
#     Template views
# =======================


def index(request):
    """ Home page """
    if request.user.is_superuser:
        comp_list = Company.objects.filter()
        return render(request, "polls/index.html", locals())
    elif request.user.is_authenticated:
        user_comp = UserComp.objects.get(user=request.user)
        return redirect("polls:company_home", comp_slug=user_comp.company.comp_slug)
    else:
        return render(request, "polls/index.html", locals())


@login_required
def company_home(request, comp_slug):
    """ Company's home page """
    # Display event list
    company = Company.get_company(comp_slug)
    next_event_list = Event.get_next_events(company)
    return render(request, "polls/company_home.html", locals())


@login_required
def event(request, comp_slug, event_slug):
    """ Event details page """

    # Define event context
    # company = Company.get_company(comp_slug)
    event = Event.get_event(comp_slug, event_slug)
    question_list = Question.get_question_list(event)
    nb_questions = len(question_list)

    # Check if connected user is part of the event and is authorized to vote
    user_can_vote = False
    if EventGroup.user_in_event(event_slug, request.user.usercomp):
        user_can_vote = True

        # Get user's proxy status
        proxy_list, user_proxy, user_proxy_list = Procuration.get_proxy_status(
            event_slug, request.user.usercomp
        )

    return render(request, "polls/event.html", locals())


@login_required
def question(request, comp_slug, event_slug, question_no):
    """ Questions details page 
        Manage information display """

    # Necessary info for the template
    # company = Company.get_company(comp_slug)
    event = Event.get_event(comp_slug, event_slug)
    evt_group_list = EventGroup.get_list(event_slug)
    question = Question.get_question(event, question_no)
    choice_list = Choice.get_choice_list(event_slug)
    last_question = False

    # Start event - occur when staff only used "Launch event" button
    if request.user.is_staff and not event.current:
        # Event can be launched only if total groups' weight == 100
        if (
            EventGroup.objects.filter(event=event).aggregate(Sum("weight"))[
                "weight__sum"
            ]
            != 100
        ):
            return redirect("polls:event", comp_slug=comp_slug, event_slug=event_slug)
        else:
            # Initialize users vote & results table
            init_event(event)

    # Gather user's info about the current question
    if not request.user.is_staff:
        user_vote = UserVote.get_user_vote(event_slug, request.user.usercomp, question_no)

    # Check if current question is the last one
    if question_no == len(Question.get_question_list(event)):
        last_question = True

    return render(request, "polls/question.html", locals())


@login_required
def results(request, comp_slug, event_slug):
    """ Results page """

    # company = Company.get_company(comp_slug)
    event = Event.get_event(comp_slug, event_slug)
    question_list = Question.get_question_list(event)
    nb_questions = len(question_list)

    return render(request, "polls/results.html", locals())


# =======================
#      Action views
# =======================


def get_chart_data(request):
    """ Gather and send information to build charts via ajax get request """

    comp_slug = request.GET["comp_slug"]
    event_slug = request.GET["event_slug"]
    question_no = int(request.GET["question_no"])

    event = Event.get_event(comp_slug, event_slug)
    evt_group_list = EventGroup.get_list(event_slug)

    data = set_chart_data(event, evt_group_list, question_no)

    return JsonResponse(data)


def vote(request, comp_slug, event_slug, question_no):
    """ Manage users' votes """

    choice_id = request.POST["choice"]
    user_vote = UserVote.set_vote(event_slug, request.user.usercomp, question_no, choice_id)

    data = {"success": "OK", "nb_votes": user_vote.nb_user_votes}

    return JsonResponse(data)


def set_proxy(request):
    """ Set proxyholder """

    user = User.objects.get(id=request.POST["user"])
    proxy = User.objects.get(id=request.POST["proxy"])
    event = Event.get_event(request.POST["comp_slug"], request.POST["event_slug"])

    Procuration.set_user_proxy(event, user, proxy)
    PollsMail(
        "ask_proxy",
        event,
        sender=[user.email],
        recipient_list=[proxy.email],
        user=user,
        proxy=proxy,
    )

    data = {
        "proxy_f_name": proxy.first_name,
        "proxy_l_name": proxy.last_name,
        "proxy": request.POST["proxy"],
    }

    return JsonResponse(data)


def accept_proxy(request):
    """ Accept proxy request """

    user = User.objects.get(id=request.POST["user"])
    # decode list sent in JSON format
    proxy_list = json.loads(request.POST["cancel_list"])

    event = Event.get_event(request.POST["comp_slug"], request.POST["event_slug"])

    for proxy_id in proxy_list:
        Procuration.confirm_proxy(event, user, int(proxy_id))
        PollsMail(
            "confirm_proxy", event, sender=[user.email], user=user, proxy_id=proxy_id
        )

    data = {"status": "Success"}

    return JsonResponse(data)


def cancel_proxy(request):
    """ Cancel or refuse proxy """

    event_slug = request.POST["event"]

    if request.POST["Action"] == "Refuse":
        proxy_list = request.POST.getlist("user_proxy")
        for proxy in proxy_list:
            Procuration.cancel_proxy(event_slug, int(proxy), request.user)
    else:
        Procuration.cancel_proxy(event_slug, request.user)

    return redirect("polls:event", event_slug=event_slug)


# ========================================
#      Administration views & actions
# ========================================


def admin_polls(request, comp_slug, admin_id):
    # company = Company.get_company(comp_slug)
    access_admin = False
    current_user = request.user
    if current_user.is_authenticated and UserComp.objects.filter(user=current_user):
        # Checks that user is connected and UserComp exists for him
        if current_user.usercomp.company.comp_slug == comp_slug and current_user.usercomp.is_admin:
            # The user needs to belong to the company and have admin role
            access_admin = True

    if access_admin:
        # Operations performed for authorized users
        if request.method == 'POST':
            # A form (user creation or update) has been submitted
            user_form = UserBaseForm(request.POST)
            usercomp_form = UserCompForm(request.POST)
            if user_form.is_valid() and usercomp_form.is_valid():
                if admin_id == 2:
                    # User management
                    username = user_form.cleaned_data["username"]
                    # password = user_form.cleaned_data["password"]
                    if User.objects.filter(username=username):
                        user_exists = True
                    else:
                        # Save new user first
                        #   Use create_user method (instead of form.save()) to include password validation
                        new_user = User.objects.create_user(
                            username=username,
                            password=user_form.cleaned_data["password"],
                            last_name=user_form.cleaned_data["last_name"],
                            first_name=user_form.cleaned_data["first_name"],
                            email=user_form.cleaned_data["email"]
                            )
                        # Save UserComp
                        #   - create the object without saving
                        #   - add user and finally validate
                        usr_comp = usercomp_form.save(commit=False)
                        usr_comp.company = Company.get_company(comp_slug)
                        usr_comp.user = new_user
                        usr_comp.save()
                else:
                    # To be defined
                    x = 1
        else:
            # Send form details for user cretation or modification
            user_form = UserBaseForm()
            usercomp_form = UserCompForm()

        user_list = UserComp.objects.order_by('user__last_name').filter(company__comp_slug=comp_slug)
        # user_form = UserBaseForm()
        # usercomp_form = UserCompForm()
        return render(request, "polls/admin_polls.html", locals())
    else:
        # User is not authorized to go to the page : back to home page
        return redirect("polls:index")


def create_user(request, comp_slug):
    if request.method == 'POST':
        # A form (user creation or update) has been submitted
        user_form = UserBaseForm(request.POST)
        usercomp_form = UserCompForm(request.POST)
        if user_form.is_valid() and usercomp_form.is_valid():
            username = user_form.cleaned_data["username"]
            # password = user_form.cleaned_data["password"]
            if User.objects.filter(username=username):
                user_exists = True
            else:
                # Save new user first
                #   Use create_user method (instead of form.save()) to include password validation
                new_user = User.objects.create_user(
                    username=username,
                    password=user_form.cleaned_data["password"],
                    last_name=user_form.cleaned_data["last_name"],
                    first_name=user_form.cleaned_data["first_name"],
                    email=user_form.cleaned_data["email"]
                    )
                # Save UserComp
                #   - create the object without saving
                #   - add user and finally validate
                usr_comp = usercomp_form.save(commit=False)
                usr_comp.company = Company.get_company(comp_slug)
                usr_comp.user = new_user
                usr_comp.save()
        return redirect("polls:admin_polls", comp_slug=comp_slug, admin_id=2)
    else:
        # Send form details for user cretation or modification
        user_form = UserBaseForm()
        usercomp_form = UserCompForm()


def update_user(request, comp_slug, usr_id):
    current_user = User.objects.get(pk=usr_id)
    UserCompFormSet = inlineformset_factory(User, UserComp, fields=('title',))
    if request.method == "POST":
        formset = UserCompFormSet(request.POST, request.FILES, instance=current_user)
        if formset.is_valid():
            formset.save()
            # Do something. Should generally end with a redirect. For example:
            return redirect("polls:admin_polls", comp_slug=comp_slug, admin_id=2)
    else:
        formset = UserCompFormSet(instance=current_user)
    # return render(request, 'manage_books.html', {'formset': formset})
    # return render(request, "polls/admin_polls.html", locals())
    return HttpResponse(render_to_string('polls/user_update_success.html', {'user': current_user}))


class UpdateUserView(FormView):
    model = User
    form_class = UserBaseForm
    template_name = 'polls/update_user.html'

    def dispatch(self, *args, **kwargs):
        self.item_id = kwargs['pk']
        return super(UpdateUserView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.save()
        user = User.objects.get(id=self.user_id)
        return HttpResponse(render_to_string('polls/user_update_success.html', {'user': user}))


class DeleteUserView(FormView):
    model = User
    template_name = 'polls/delete_user.html'
    form_class = UserBaseForm
    success_message = 'Utilisateur supprimé avec succès.'
    success_url = reverse_lazy('admin_polls')
