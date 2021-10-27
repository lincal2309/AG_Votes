# -*-coding:Utf-8 -*

''' Tools for Votes app '''
import random
# from django.conf import settings

from django.utils import timezone
import datetime
from django.conf import settings

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

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

from django.utils.text import slugify



# debug = settings.DEBUG

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




# ===================================
#  Global functions used for testing
# ===================================


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
    usrcomp = UserComp.objects.create(company=company, user=usr, is_admin=admin)
    usrcomp.save()

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
        # street_num=1,
        # street_cplt='',
        address1="Rue des fauvettes",
        # address2='',
        zip_code="99456",
        city='Somewhere',
        host="smtp.gmail.com",
        port=587,
        hname="test@polls.com",
        fax="toto",
    )

# def add_dummy_event(company, name="Dummy event", groups=None, new_groups=True):
#     # Create dummy event and add group if any
#     # Allows to test case were more than 1 event is in the database
#     event_date = timezone.now() + datetime.timedelta(days=1)
#     event = Event.objects.create(
#         company=company,
#         event_name=name,
#         event_date=event_date,
#         slug=slugify(name + str(event_date)),
#     )
#     Question.objects.create(
#         question_text="Dummy quest 1", question_no=1, event=event
#     )
#     Question.objects.create(
#         question_text="Dummy quest 2", question_no=2, event=event
#     )
#     Choice.objects.create(
#         event=event, choice_text="Dummy choice 1", choice_no=1
#     )
#     Choice.objects.create(
#         event=event, choice_text="Dummy choice 2", choice_no=2
#     )
    
#     if groups is not None:
#         # Add groups to event if any
#         for group in groups:
#             event.groups.add(group)
#     else:
#         groups = []

#     if new_groups:
#         # Create dummy groups if requested
#         group1 = EventGroup.objects.create(group_name="Dummy group 1", weight=30)
#         group2 = EventGroup.objects.create(group_name="Dummy group 2", weight=70)
#         event.groups.add(group1, group2)
#         groups += [group1, group2]

#     if len(groups) > 0:
#         # if groups sent and / or created, create results and uservotes
#         for group in groups:
#             create_dummy_user(company, "user " + group.group_name + " 1", group=group)
#             create_dummy_user(company, "user " + group.group_name + " 2", group=group)

#         init_event(event)
