# -*-coding:Utf-8 -*

''' Tools for Votes app '''
import random
# from django.conf import settings

from django.conf import settings
from django.utils import timezone
import datetime
from django.db.models import Count

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import (
    Company,
    Event,
    Question,
    Choice,
    UserVote,
    UserGroup,
    Result,
    Procuration,
    UserComp,
)


debug = settings.DEBUG
background_colors = settings.BACKGROUND_COLORS
border_colors = settings.BORDER_COLORS


# Generate secured password
pass_length = 10
pass_chars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
              "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
              "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
              "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
              "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
              "&", "(", "-", "_", ")", "=", "#", "{", "[", "|", "\\", "@", "]",
              "}", "$", "%", "*", "?", "/", "!", "§", "<", ">"]

def define_password():
    result = "".join([random.choice(pass_chars) for x in range(0, pass_length)])
    # if debug:
    #     result = "titi"
    return result


# =======================
#    Global functions
# =======================


def create_new_user(comp_slug, user_data):
    ''' Function used to create new user '''

    username = user_data["username"]
    # password = user_form.cleaned_data["password"]
    if User.objects.filter(username=username):
        user_exists = True
    else:
        # Save new user first
        if "password" not in user_data:
            user_data["password"] = username.lower()
        new_user = User.objects.create_user(
            username=username,
            password=user_data["password"],
            last_name=user_data["last_name"],
            first_name=user_data["first_name"],
            email=user_data["email"]
            )

        if comp_slug != '':
            company = Company.get_company(comp_slug)
            usr_comp = UserComp.create_usercomp(
                user=new_user, 
                company=company,
                phone_num=user_data["phone_num"],
                is_admin=user_data["is_admin"]
            )
        else:
            usr_comp = ''

    return new_user, usr_comp


def user_is_admin(comp_slug, current_user):
    """
    Check whether current user has admin access or not (for his company)
    """
    access_admin = False
    if current_user.is_authenticated and UserComp.objects.filter(user=current_user):
        # Checks that user is connected and UserComp exists for him
        if current_user.usercomp.company.comp_slug == comp_slug and current_user.usercomp.is_admin:
            # The user needs to belong to the company and have admin role
            access_admin = True

    return access_admin


def init_event(event):
    """
    Initialize an event and set it as current
    """
    UserVote.init_uservotes(event)
    event.set_current()


def set_chart_data(event, evt_group_list, question_no):
    """
    Define data to display related charts
    """

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
        total_votes = UserGroup.objects.filter(id=evt_group.id).aggregate(
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
