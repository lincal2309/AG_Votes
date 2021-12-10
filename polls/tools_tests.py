# -*-coding:Utf-8 -*

''' Global functions used for testing '''

from django.utils import timezone
import datetime
from django.conf import settings
from django.utils.text import slugify

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

from .tools import init_event



def create_dummy_user(company, username, group=None, staff=False, admin=False):
    email = username + "@toto.com"
    last_name = "nom_" + username
    usr = User.objects.create_user(
        username=username,
        password=username,
        is_superuser=staff,
        is_staff=staff,
        email=email,
        last_name=last_name
    )
    usrcomp = UserComp.create_usercomp(usr, company, is_admin=admin)

    if group:
        group.users.add(usrcomp)
    return usrcomp


def create_dummy_company(name):
    return Company.objects.create(
        company_name=name,
        comp_slug=slugify(name),
        logo=SimpleUploadedFile(name='logo.jpg', content=b'content', content_type='image/jpeg'),
        statut="SARL",
        siret="0123456789",
        address1="Rue des fauvettes",
        zip_code="99456",
        city='Somewhere',
        host="smtp.gmail.com",
        port=587,
        hname="test@polls.com",
        fax="toto",
    )


def create_dummy_event(company, name="Dummy event", event_start_date=None, current=False, groups=[], new_groups=True):
    # Create dummy event and add groups if any
    if event_start_date is None: event_start_date = timezone.now() + datetime.timedelta(days=1)
    event = Event.create_event(company, name, event_start_date, current=current, groups=groups)

    Question.create_question(event, 1, "Question 1")
    Question.create_question(event, 2, "Question 2")

    Choice.create_choice(event, 1, "Choix 1")
    Choice.create_choice(event, 2, "Choix 2")
    
    groups = list(UserGroup.get_group_list(event))

    if new_groups:
        # Create dummy groups if requested
        group1 = UserGroup.create_group(company, "Groupe 1", weight=30)
        group2 = UserGroup.create_group(company, "Groupe 2", weight=70)
        event.groups.add(group1, group2)
        groups += [group1, group2]

    return event


def set_default_context():
    company = create_dummy_company("Société de test")

    user_staff = create_dummy_user(company, "staff", admin=True)
    usr11 = create_dummy_user(company, "user11")
    usr12 = create_dummy_user(company, "user12", admin=True)
    usr13 = create_dummy_user(company, "user13")
    usr14 = create_dummy_user(company, "user14")
    usr21 = create_dummy_user(company, "user21")
    usr22 = create_dummy_user(company, "user22")

    user_list = [usr11.id, usr12.id, usr13.id, usr14.id]
    users = UserComp.objects.filter(id__in=user_list)
    group1 = UserGroup.create_group(company, "Groupe 1", weight=40, user_list=users)

    user_list = [usr21.id, usr22.id]
    users = UserComp.objects.filter(id__in=user_list)
    group2 = UserGroup.create_group(company, "Groupe 2", weight=60, user_list=users)

    group_list = [group1, group2]
    event1 = create_dummy_event(company, name="Event 1", groups=group_list, new_groups=False)
    group_list = [group1]
    event2 = create_dummy_event(company, name="Event 2", groups=group_list, new_groups=False)
    event3 = create_dummy_event(company, name="Event 3", groups=group_list, new_groups=False)
    event3.event_start_date = timezone.now() + datetime.timedelta(days=-10)
    event3.save()

    test_data = {
        "company": company,

        "user_staff": user_staff,
        "usr11": usr11,
        "usr12": usr12,
        "usr13": usr13,
        "usr14": usr14,
        "usr21": usr21,
        "usr22": usr22,

        "group1": group1,
        "group2": group2,

        "event1": event1,
        "event2": event2,
        "event3": event3,

        "question_list_1": Question.get_question_list(event1),
        "choice_list_1": Choice.get_choice_list(event1)
    }

    return test_data

def set_full_context():
    test_data = set_default_context()

    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group1"],
        question=test_data["question_list_1"][0],
        choice=test_data["choice_list_1"][0],
        votes=3,
        group_weight=30,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group1"],
        question=test_data["question_list_1"][0],
        choice=test_data["choice_list_1"][1],
        votes=1,
        group_weight=30,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group1"],
        question=test_data["question_list_1"][1],
        choice=test_data["choice_list_1"][0],
        votes=1,
        group_weight=30,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group1"],
        question=test_data["question_list_1"][1],
        choice=test_data["choice_list_1"][1],
        votes=3,
        group_weight=30,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group2"],
        question=test_data["question_list_1"][0],
        choice=test_data["choice_list_1"][0],
        votes=0,
        group_weight=70,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group2"],
        question=test_data["question_list_1"][0],
        choice=test_data["choice_list_1"][1],
        votes=2,
        group_weight=70,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group2"],
        question=test_data["question_list_1"][1],
        choice=test_data["choice_list_1"][0],
        votes=0,
        group_weight=70,
    )
    Result.objects.create(
        event=test_data["event1"],
        usergroup=test_data["group2"],
        question=test_data["question_list_1"][1],
        choice=test_data["choice_list_1"][1],
        votes=2,
        group_weight=70,
    )

    return test_data
