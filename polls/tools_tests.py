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
    # usrcomp.save()

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

    # return Company.create_company(
    # name,
    # "SARL",
    # "0123456789",
    # "Rue des fauvettes",
    # "99456",
    # "Somewhere",
    # logo="logo.jpg",
    # host="smtp.gmail.com",
    # port=587,
    # hname="test@polls.com",
    # fax="toto"
    # )



def create_dummy_event(company, name="Dummy event", groups=None, new_groups=True):
    # Create dummy event and add group if any
    # Allows to test case were more than 1 event is in the database
    event_date = timezone.now() + datetime.timedelta(days=1)
    event = Event.objects.create(
        company=company,
        event_name=name,
        event_date=event_date,
        slug=slugify(name + str(event_date)),
    )
    Question.create(event, 1, "Dummy quest 1")
    Question.create(event, 2, "Dummy quest 2")

    Choice.create(event, 1, "Dummy choice 1")
    Choice.create(event, 2, "Dummy choice 2")
    
    if groups is not None:
        # Add groups to event if any
        for group in groups:
            event.groups.add(group)
    else:
        groups = []

    if new_groups:
        # Create dummy groups if requested
        group1 = UserGroup.create_group(company, "Dummy group 1", 30)
        group2 = UserGroup.create_group(company, "Dummy group 2", 70)
        event.groups.add(group1, group2)
        groups += [group1, group2]

    # if len(groups) > 0:
    #     # if groups sent and / or created, create results and uservotes
    #     for group in groups:
    #         if UserComp.objects.filter(usergroup=group).count() == 0:
    #             create_dummy_user(company, "user " + group.group_name + " 1", group=group)
    #             create_dummy_user(company, "user " + group.group_name + " 2", group=group)

    #     init_event(event)

    return event
