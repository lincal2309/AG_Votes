# -*-coding:Utf-8 -*

from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import reverse, get_list_or_404, get_object_or_404
from django.contrib.auth.models import User
from django.core import mail
from django.core.files import File
from django.conf import settings
# from django.db.models import Sum

# from unittest import mock

import os
import datetime

from .tools_tests import (
    create_dummy_user,
    create_dummy_company,
    add_dummy_event,
)

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

from .tools import set_chart_data, init_event
from .pollsmail import PollsMail


# ===================================
#  Test global functions & utilities
# ===================================


class TestSetChartData(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )
        self.choice1 = Choice.objects.create(
            event=self.event, choice_text="Choix 1", choice_no=1
        )
        self.choice2 = Choice.objects.create(
            event=self.event, choice_text="Choix 2", choice_no=2
        )
        self.group1 = EventGroup.objects.create(group_name="Groupe 1", weight=30)
        self.group2 = EventGroup.objects.create(group_name="Groupe 2", weight=70)
        self.event.groups.add(self.group1, self.group2)
        Result.objects.create(
            event=self.event,
            eventgroup=self.group1,
            question=self.question1,
            choice=self.choice1,
            votes=3,
            group_weight=30,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group1,
            question=self.question1,
            choice=self.choice2,
            votes=1,
            group_weight=30,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group1,
            question=self.question2,
            choice=self.choice1,
            votes=1,
            group_weight=30,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group1,
            question=self.question2,
            choice=self.choice2,
            votes=3,
            group_weight=30,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group2,
            question=self.question1,
            choice=self.choice1,
            votes=0,
            group_weight=70,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group2,
            question=self.question1,
            choice=self.choice2,
            votes=2,
            group_weight=70,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group2,
            question=self.question2,
            choice=self.choice1,
            votes=0,
            group_weight=70,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group2,
            question=self.question2,
            choice=self.choice2,
            votes=2,
            group_weight=70,
        )
        self.usr11 = create_dummy_user(self.company, "user11", self.group1)
        self.usr12 = create_dummy_user(self.company, "user12", self.group1)
        self.usr13 = create_dummy_user(self.company, "user13", self.group1)
        self.usr14 = create_dummy_user(self.company, "user14", self.group1)
        self.usr21 = create_dummy_user(self.company, "user21", self.group2)
        self.usr22 = create_dummy_user(self.company, "user22", self.group2)

        add_dummy_event(self.company)


    def test_chart_first_question_maj(self):
        evt_group_list = EventGroup.get_list(self.event.slug)
        data = set_chart_data(self.event, evt_group_list, 1)

        # Global variables
        self.assertEqual(data["nb_charts"], 2)

        # Global data
        global_data = data["chart_data"]["global"]
        self.assertEqual(global_data["labels"], ["Choix 1", "Choix 2"])
        self.assertEqual(global_data["values"], [30, 70])
        self.assertEqual(global_data["nb_votes"], 6)
        self.assertEqual(global_data["total_votes"], 6)

        # Group 1 data
        group_data = data["chart_data"]["chart1"]
        self.assertEqual(group_data["values"], [3, 1])
        self.assertEqual(group_data["nb_votes"], 4)
        self.assertEqual(group_data["total_votes"], 4)

    def test_get_results_prop(self):
        Event.objects.filter(id=self.event.id).update(rule="PROP")
        self.event.refresh_from_db()

        evt_group_list = EventGroup.get_list(self.event.slug)
        data = set_chart_data(self.event, evt_group_list, 1)
        global_data = data["chart_data"]["global"]

        # Global data
        self.assertEqual(global_data["values"], [34.62, 65.38])

        # Group 1 data
        group_data = data["chart_data"]["chart1"]
        self.assertEqual(group_data["values"], [3, 1])

    def test_get_results_prop_not_all_questions_answered(self):
        Result.objects.filter(question=self.question2).delete()
        Event.objects.filter(id=self.event.id).update(rule="PROP")
        self.event.refresh_from_db()

        evt_group_list = EventGroup.get_list(self.event.slug)
        data = set_chart_data(self.event, evt_group_list, 1)
        global_data = data["chart_data"]["global"]

        # Global data
        self.assertEqual(global_data["values"], [34.62, 65.38])

        # Group 1 data
        group_data = data["chart_data"]["chart1"]
        self.assertEqual(group_data["values"], [3, 1])


class TestPollsMail(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )
        self.group1 = EventGroup.objects.create(group_name="Groupe 1", weight=30)
        self.group2 = EventGroup.objects.create(group_name="Groupe 2", weight=70)
        self.event.groups.add(self.group1, self.group2)
        self.usr11 = create_dummy_user(self.company, "user11", self.group1)
        self.usr12 = create_dummy_user(self.company, "user12", self.group1)
        self.usr13 = create_dummy_user(self.company, "user13", self.group1)
        self.usr14 = create_dummy_user(self.company, "user14")
        self.usr21 = create_dummy_user(self.company, "user21", self.group2)
        self.usr22 = create_dummy_user(self.company, "user22", self.group2)

    def test_ask_proxy_message(self):
        PollsMail(
            "ask_proxy",
            self.event,
            sender=[self.usr11.user.email],
            recipient_list=[self.usr13.user.email],
            user=self.usr11,
            proxy=self.usr13,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Pouvoir")

    def test_confirm_proxy_message(self):
        PollsMail(
            "confirm_proxy",
            self.event,
            sender=[self.usr11.user.email],
            user=self.usr11,
            proxy_id=self.usr12.id,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Confirmation de pouvoir")

    def test_invite_users_message(self):
        # Create dummy file
        with open(os.path.join(settings.MEDIA_ROOT, "pdf/test_file.pdf"), "w") as f:
            dummy_file = File(f)
            dummy_file.write("Liste des résolutions")

        PollsMail("invite", self.event, attach="pdf/test_file.pdf")
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[0].subject, "Invitation et ordre du jour")



# ===================================
#        Test admin actions
# ===================================


class TestAdminActions(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug="event-test",
            company=self.company,
        )

        self.group1 = EventGroup.objects.create(group_name="Groupe 1", weight=30)
        self.group2 = EventGroup.objects.create(group_name="Groupe 2", weight=70)
        self.event.groups.add(self.group1, self.group2)

        create_dummy_user(self.company, "user11", self.group1)
        create_dummy_user(self.company, "user12", self.group1)
        create_dummy_user(self.company, "user13", self.group1)
        create_dummy_user(self.company, "user14")
        create_dummy_user(self.company, "user21", self.group2)
        create_dummy_user(self.company, "user22", self.group2)

        superusr = User.objects.create_superuser(
            username="test", password="test", email="test@test.py"
        )
        self.client.force_login(superusr)

    def test_info_company(self):
        data = {"action": "test_email", "_selected_action": [self.company.id]}

        url = reverse("admin:polls_company_changelist")
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_invite_users_total_group_weight_not_100(self):
        EventGroup.objects.filter(id=self.group1.id).update(weight=10)
        self.group1.refresh_from_db()

        data = {"action": "invite_users", "_selected_action": [self.event.id]}
        url = reverse("admin:polls_event_changelist")

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_users(self):

        data = {"action": "invite_users", "_selected_action": [self.event.id]}
        url = reverse("admin:polls_event_changelist")

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[0].subject, "Invitation et ordre du jour")
