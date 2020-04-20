# -*-coding:Utf-8 -*

from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
# from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Sum
from django.conf import settings
# from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
# from django.core.exceptions import ValidationError
from django.core.files import File
# from django.forms import inlineformset_factory

from django.urls import reverse_lazy, resolve
# from django.views.generic.edit import FormView
# from django.views.generic.list import ListView

import openpyxl

import re

from .forms import UserBaseForm, UserCompForm, UploadFileForm
from .tools import define_password

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

def create_new_user(comp_slug, user_data):
    ''' Function used to create new user '''
    username = user_data["username"]
    # password = user_form.cleaned_data["password"]
    if User.objects.filter(username=username):
        user_exists = True
    else:
        # Save new user first
        #   Use create_user method (instead of form.save()) to include password validation
        new_pass = username.lower()
        new_user = User.objects.create_user(
            username=username,
            password=new_pass,
            last_name=user_data["last_name"],
            first_name=user_data["first_name"],
            email=user_data["email"]
            )
        # new_user.save()
        # Save UserComp
        #   - create the object without saving
        #   - add user and finally validate
        company = Company.get_company(comp_slug)
        usr_comp = UserComp.create_usercomp(
            user=new_user, 
            company=company,
            email=user_data["phone_number"],
            is_admin=user_data["is_admin"]
        )
    return new_user, usr_comp


@login_required
def admin_events(request, comp_slug):
    '''
        Manage events creation and options
    '''
    access_admin = False
    current_user = request.user
    if current_user.is_authenticated and UserComp.objects.filter(user=current_user):
        # Checks that user is connected and UserComp exists for him
        if current_user.usercomp.company.comp_slug == comp_slug and current_user.usercomp.is_admin:
            # The user needs to belong to the company and have admin role
            access_admin = True

    if access_admin:
        return render(request, "polls/admin_events.html", locals())
    else:
        # User is not authorized to go to the page : back to home page
        return redirect("polls:index")


# @user_passes_test(lambda u: u.is_superuser)
@login_required
def admin_users(request, comp_slug):
    '''
        Manage users
    '''
    access_admin = False
    current_user = request.user
    if current_user.is_authenticated and UserComp.objects.filter(user=current_user):
        # Checks that user is connected and UserComp exists for him
        if current_user.usercomp.company.comp_slug == comp_slug and current_user.usercomp.is_admin:
            # The user needs to belong to the company and have admin role
            access_admin = True

    if access_admin:
        user_list = UserComp.objects.order_by('user__last_name').filter(company__comp_slug=comp_slug)
        upload_form = UploadFileForm()
        return render(request, "polls/admin_users.html", locals())
    else:
        # User is not authorized to go to the page : back to home page
        return redirect("polls:index")

@login_required
def user_profile(request, comp_slug, usr_id=0):
    if usr_id > 0:
        current_user = User.objects.get(pk=usr_id)
        user_form = UserBaseForm(request.POST or None, instance=current_user)
        usercomp_form = UserCompForm(request.POST or None, instance=current_user.usercomp)
    else:
        user_form = UserBaseForm(request.POST or None)
        usercomp_form = UserCompForm(request.POST or None)
    
    if request.method == 'POST':
        if user_form.is_valid() and usercomp_form.is_valid():
            if usr_id == 0:
                # New user
                user_data = {
                    'username':  user_form.cleaned_data["username"],
                    'last_name': user_form.cleaned_data["last_name"],
                    'first_name': user_form.cleaned_data["first_name"],
                    'email': user_form.cleaned_data["email"],
                    'phone_num': usercomp_form.cleaned_data["phone_num"],
                    'is_admin': usercomp_form.cleaned_data["is_admin"],
                }
                new_user, usr_comp = create_new_user(comp_slug, user_data)
                msg = "Utilisateur {0} {1} créé avec succès".\
                    format(new_user.last_name, new_user.first_name)
                messages.success(request, msg)
            else:
                # Update user
                upd_user = user_form.save()
                usercomp_form.save()

                if upd_user == request.user:
                    msg = ("Votre profil a été modifié avec succès.")
                else:
                    msg = "Utilisateur {0} {1} modifié avec succès.".\
                        format(upd_user.last_name, upd_user.first_name)
        
                messages.success(request, msg)
            
            # Redirect to previous page (referer)
            url_dest = "polls:" + request.POST['url_dest']
            return redirect(url_dest, comp_slug=comp_slug)

    # Store referer (page that called the view) to be able to go back to the page
    ref_origin = request.META['HTTP_REFERER']
    host = request.META['HTTP_HOST']
    url_ref = ref_origin.replace("http://", "").replace(host, "")
    url_match = resolve(url_ref)
    url_dest = url_match.url_name
    return render(request, "polls/user_profile.html", locals())


@login_required
def change_password(request, comp_slug):
    if request.method == 'POST':
        pwd_form = PasswordChangeForm(request.user, request.POST)
        if pwd_form.is_valid():
            user = pwd_form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Mot de passe modifié avec succès.')
            return redirect('polls:user_profile', comp_slug=comp_slug, usr_id=request.user.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        pwd_form = PasswordChangeForm(request.user)

    # return render(request, 'polls/change_pwd.html', {
    #     'form': pwd_form,
    #     'comp_slug': comp_slug,
    # })
    return render(request, "polls/change_pwd.html", locals())
        


@login_required
def delete_user(request, comp_slug, usr_id):
    del_usr = User.objects.get(pk=usr_id)
    msg = "Utilisateur {0} {1} supprimé.".\
            format(del_usr.last_name, del_usr.first_name)

    User.objects.filter(pk=usr_id).delete()

    messages.success(request, msg)
    return redirect("polls:admin_users", comp_slug=comp_slug)


@login_required
def load_users(request, comp_slug):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['file']

            wb = openpyxl.load_workbook(f)
            sheet = request.POST['sheet']
            ws = wb[sheet]

            # Check the files has the required information
            elt_list = ['Nom', 'Prénom', 'Mail', 'Téléphone', 'Username']

            # Gather values in file's first row - supposed to be headers to retreive data
            header = ws[1]
            titles = [cell.value for cell in header]

            try:
                index_list = [titles.index(elt) for elt in elt_list]
            except:
                messages.error(request, "Chargement du fichier impossible : la structure ne correspond pas à ce qui est attendu")
                return redirect("polls:admin_users", comp_slug=comp_slug)

            nb_lines = 0
            nb_warn = 0
            nb_err = 0
            err_messages = []
            warn_messages = []

            for row in ws.iter_rows(min_row=2, values_only=True):
                nb_lines += 1
                unique_user = True

                last_name = row[0]
                first_name = row[1]
                email = row[2]
                phone_num = row[3]
                if row[4] is not None:
                    username = row[4]
                else:
                    username = last_name.lower()

                # Data controls :
                # - user unicity : if username alreay exists;
                #       * for provided usernames, raise an error and reject line
                #       * else (username == last_name) : check first name and email
                #           if both are equal, reject row
                #           else : define new id with first-name chars
                # - phone numer format (warning only)

                if User.objects.filter(username=username).exists():
                    db_user = User.objects.get(username=username)
                    if (db_user.last_name == last_name and db_user.first_name == first_name \
                                                      and db_user.email == email) \
                        or (row[4] is not None):
                        # user already exists
                        nb_err += 1
                        err_messages.insert(0, "Utilisateur {0} {1} non créé : il existe déjà".format(last_name, first_name))
                        continue  # directly goes no next iteration

                    else:
                        unique_user = False
                        i = 0
                        while unique_user == False:
                            username += first_name.lower()[i:i+1]
                            i += 1
                            if User.objects.filter(username=username).exists():
                                # It's another user than before : needs to check unicity again
                                db_user = User.objects.get(username=username)
                                if (db_user.last_name == last_name and db_user.first_name == first_name \
                                                                and db_user.email == email) \
                                    or (row[4] is not None):
                                    # user already exists
                                    nb_err += 1
                                    err_messages.insert(0, "Utilisateur {0} {1} non créé : il existe déjà".format(last_name, first_name))
                                    break

                                elif i >= len(first_name.lower()):
                                    # Not able to automatically define a unique username
                                    nb_err += 1
                                    err_messages.insert(0, "Utilisateur {0} {1} non créé : impossible de définir un nom d'utilisateur unique".format(last_name, first_name))
                                    break
                            else:
                                unique_user = True

                # Out of while loop : check if a unique username has been found
                if unique_user is True:
                    if phone_num is not None and not re.match(r'^0[0-9]([ .-]?[0-9]{2}){4}$', str(phone_num)):
                        phone_num = ''    # integrate no phone number rather than invalid one
                        nb_warn += 1
                        warn_messages.insert(0, "Utilisateur {0} {1} : numéro de téléphone invalide".format(last_name, first_name))

                    # Create user & usercomp
                    new_user = User.objects.create_user(
                        username=username,
                        password=username,
                        last_name=last_name,
                        first_name=first_name,
                        email=email
                    )

                    company = Company.get_company(comp_slug)
                    usr_comp = UserComp.create_usercomp(
                        user=new_user,
                        company=company,
                        phone_num=phone_num
                    )
            
            # Messages are created at the end to ensure having the right order
            msg = "{0} utilisateurs sur {1} correctement intégrés, {2} avertissement(s).".format((nb_lines - nb_err), nb_lines, nb_warn)
            messages.success(request, msg)

            for err_msg in err_messages:
                messages.error(request, err_msg)
            for warn_msg in warn_messages:
                messages.warning(request, warn_msg)

            return redirect("polls:admin_users", comp_slug=comp_slug)


@login_required
def admin_groups(request, comp_slug):
    '''
        Manage users groups
    '''
    access_admin = False
    current_user = request.user
    if current_user.is_authenticated and UserComp.objects.filter(user=current_user):
        # Checks that user is connected and UserComp exists for him
        if current_user.usercomp.company.comp_slug == comp_slug and current_user.usercomp.is_admin:
            # The user needs to belong to the company and have admin role
            access_admin = True

    if access_admin:
        return render(request, "polls/admin_groups.html", locals())
    else:
        # User is not authorized to go to the page : back to home page
        return redirect("polls:index")
