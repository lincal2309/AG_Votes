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
    create_dummy_event,
    set_default_context,
    set_full_context,
)

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

from .tools import set_chart_data, init_event
from .pollsmail import PollsMail


# ===================================
#  Test global functions & utilities
# ===================================


class TestSetChartData(TestCase):
    def setUp(self):
        self.test_data = set_full_context()

    def test_chart_first_question_maj(self):
        evt_group_list = UserGroup.get_group_list(self.test_data["event1"])
        data = set_chart_data(self.test_data["event1"], evt_group_list, self.test_data["question_list_1"][0])

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
        self.test_data["event1"].rule = "PROP"
        self.test_data["event1"].save()

        evt_group_list = UserGroup.get_group_list(self.test_data["event1"])
        data = set_chart_data(self.test_data["event1"], evt_group_list, self.test_data["question_list_1"][0])
        global_data = data["chart_data"]["global"]

        # Global data
        self.assertEqual(global_data["values"], [34.62, 65.38])

        # Group 1 data
        group_data = data["chart_data"]["chart1"]
        self.assertEqual(group_data["values"], [3, 1])

    def test_get_results_prop_not_all_questions_answered(self):
        Result.objects.filter(question=self.test_data["question_list_1"][1]).delete()
        self.test_data["event1"].rule = "PROP"
        self.test_data["event1"].save()

        evt_group_list = UserGroup.get_group_list(self.test_data["event1"])
        data = set_chart_data(self.test_data["event1"], evt_group_list, self.test_data["question_list_1"][0])
        global_data = data["chart_data"]["global"]

        # Global data
        self.assertEqual(global_data["values"], [34.62, 65.38])

        # Group 1 data
        group_data = data["chart_data"]["chart1"]
        self.assertEqual(group_data["values"], [3, 1])


class TestPollsMail(TestCase):
    def setUp(self):
        self.test_data = set_default_context()
        # self.company = create_dummy_company("Société de test")
        # event_start_date = timezone.now() + datetime.timedelta(days=1)
        # self.event = Event.objects.create(
        #     event_name="Evénement de test",
        #     event_start_date=event_start_date,
        #     slug=slugify("Evénement de test" + str(event_start_date)),
        #     company=self.company,
        # )
        # self.question1 = Question.objects.create(
        #     question_text="Question 1", question_no=1, event=self.event
        # )
        # self.question2 = Question.objects.create(
        #     question_text="Question 2", question_no=2, event=self.event
        # )
        # self.group1 = UserGroup.objects.create(group_name="Groupe 1", weight=30)
        # self.group2 = UserGroup.objects.create(group_name="Groupe 2", weight=70)
        # self.event.groups.add(self.group1, self.group2)
        # self.usr11 = create_dummy_user(self.company, "user11", self.group1)
        # self.usr12 = create_dummy_user(self.company, "user12", self.group1)
        # self.usr13 = create_dummy_user(self.company, "user13", self.group1)
        # self.usr14 = create_dummy_user(self.company, "user14")
        # self.usr21 = create_dummy_user(self.company, "user21", self.group2)
        # self.usr22 = create_dummy_user(self.company, "user22", self.group2)

    def test_ask_proxy_message(self):
        PollsMail(
            "ask_proxy",
            self.test_data["event1"],
            sender=[self.test_data["usr11"].user.email],
            recipient_list=[self.test_data["usr13"].user.email],
            user=self.test_data["usr11"],
            proxy=self.test_data["usr13"],
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Pouvoir")

    def test_confirm_proxy_message(self):
        PollsMail(
            "confirm_proxy",
            self.test_data["event1"],
            sender=[self.test_data["usr11"].user.email],
            user=self.test_data["usr11"],
            proxy_id=self.test_data["usr12"].id,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Confirmation de pouvoir")

    def test_invite_users_message(self):
        # Create dummy file
        with open(os.path.join(settings.MEDIA_ROOT, "pdf/test_file.pdf"), "w") as f:
            dummy_file = File(f)
            dummy_file.write("Liste des résolutions")

        PollsMail("invite", self.test_data["event1"], attach="pdf/test_file.pdf")
        print(mail.outbox)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[0].subject, "Invitation et ordre du jour")



# ===================================
#        Test admin actions
# ===================================


class TestAdminActions(TestCase):
    def setUp(self):
        self.test_data = set_default_context()

        superusr = User.objects.create_superuser(
            username="test", password="test", email="test@test.py"
        )
        self.client.force_login(superusr)

    def test_info_company(self):
        data = {"action": "test_email", "_selected_action": [self.test_data["company"].id]}

        url = reverse("admin:polls_company_changelist")
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_invite_users_total_group_weight_not_100(self):
        self.test_data["group1"].weight = 10
        self.test_data["group1"].save()

        data = {"action": "invite_users", "_selected_action": [self.test_data["event1"].id]}
        url = reverse("admin:polls_event_changelist")

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_users(self):

        data = {"action": "invite_users", "_selected_action": [self.test_data["event1"].id]}
        url = reverse("admin:polls_event_changelist")

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[0].subject, "Invitation et ordre du jour")
