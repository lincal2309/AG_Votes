# -*-coding:Utf-8 -*

from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import reverse, get_list_or_404, get_object_or_404
from django.contrib.auth.models import User
from django.core import mail
from django.core.files import File
from django.conf import settings
from django.db.models import Sum

from unittest import mock

import os
import datetime

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
from .views import set_chart_data, init_event
from .pollsmail import PollsMail


# ===================================
#  Global functions used for testing
# ===================================


def create_dummy_user(company, username, group=None, staff=False):
    email = username + "@toto.com"
    last_name = "nom_" + username
    usr = User.objects.create_user(
        username=username, password=username, is_staff=staff, email=email, last_name=last_name
    )
    usrcomp = UserComp.objects.create(company=company, user=usr)
    usrcomp.save()

    if group:
        group.users.add(usrcomp)
    return usrcomp


def create_dummy_company(name):
    return Company.objects.create(
        company_name=name,
        comp_slug=slugify(name),
        logo="logo.png",
        statut="SARL",
        siret="0123456789",
        address1="Rue des fauvettes",
        zip_code="99456",
        host="smtp.gmail.com",
        port=587,
        hname="test@polls.com",
        fax="toto",
    )

def add_dummy_event(company, name="Dummy event", groups=None, new_groups=True):
    # Create dummy event and add group if any
    # Allows to test case were more than 1 event is in the database
    event_date = timezone.now() + datetime.timedelta(days=1)
    event = Event.objects.create(
        company=company,
        event_name=name,
        event_date=event_date,
        slug=slugify(name + str(event_date)),
    )
    Question.objects.create(
        question_text="Dummy quest 1", question_no=1, event=event
    )
    Question.objects.create(
        question_text="Dummy quest 2", question_no=2, event=event
    )
    Choice.objects.create(
        event=event, choice_text="Dummy choice 1", choice_no=1
    )
    Choice.objects.create(
        event=event, choice_text="Dummy choice 2", choice_no=2
    )
    
    if groups is not None:
        # Add groups to event if any
        for group in groups:
            event.groups.add(group)
    else:
        groups = []

    if new_groups:
        # Create dummy groups if requested
        group1 = EventGroup.objects.create(group_name="Dummy group 1", weight=30)
        group2 = EventGroup.objects.create(group_name="Dummy group 2", weight=70)
        event.groups.add(group1, group2)
        groups += [group1, group2]

    if len(groups) > 0:
        # if groups sent and / or created, create results and uservotes
        for group in groups:
            create_dummy_user(company, "user " + group.group_name + " 1", group=group)
            create_dummy_user(company, "user " + group.group_name + " 2", group=group)

        init_event(event)


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


# ===================================
#        Test models' methods
# ===================================


class TestModelCompany(TestCase):
    def test_get_company(self):
        comp = create_dummy_company("Société de test")
        company = Company.get_company("societe-de-test")
        self.assertEqual(comp.id, company.id)


class TestModelEvent(TestCase):
    def test_get_event(self):
        self.company = create_dummy_company("Société de test")
        event_date = datetime.date(2150, 5, 12)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        my_event = Event.get_event(self.company.comp_slug, "evenement-de-test2150-05-12")
        self.assertEqual(self.event, my_event)

    def test_get_next_events(self):
        company = create_dummy_company("Société de test")
        passed_date = timezone.now() - datetime.timedelta(days=1)
        future_date = timezone.now() + datetime.timedelta(days=1)
        Event.objects.create(
            event_name="Evénement passé",
            event_date=passed_date,
            slug=slugify("Evénement passé" + str(passed_date)),
            company=company,
        )
        Event.objects.create(
            event_name="Evénement futur",
            event_date=future_date,
            slug=slugify("Evénement futur" + str(future_date)),
            company=company,
        )

        next_events = Event.get_next_events(company)
        self.assertEqual(len(next_events), 1)
        self.assertEqual(next_events[0].event_name, "Evénement futur")

    def test_set_current(self):
        self.company = create_dummy_company("Société de test")
        event_date = datetime.date(2150, 5, 12)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )

        self.assertEqual(self.event.current, False)
        self.event.set_current()
        self.assertEqual(self.event.current, True)


class TestModelQuestion(TestCase):
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

    def test_get_question_list(self):
        question_list = Question.get_question_list(self.event)
        self.assertEqual(len(question_list), 2)
        self.assertEqual(question_list[0].question_text, "Question 1")
        self.assertEqual(question_list[1].question_text, "Question 2")

    def test_get_question(self):
        my_question = Question.get_question(self.event, 1)
        self.assertEqual(my_question, self.question1)

    def test_get_results_maj(self):
        group_vote = self.question1.get_results()
        self.assertEqual(group_vote["Choix 1"], 30)
        self.assertEqual(group_vote["Choix 2"], 70)
        group_vote = self.question2.get_results()
        self.assertEqual(group_vote["Choix 1"], 0)
        self.assertEqual(group_vote["Choix 2"], 100)

    def test_get_results_prop(self):
        Event.objects.filter(id=self.event.id).update(rule="PROP")
        self.event.refresh_from_db()
        group_vote = self.question1.get_results()
        self.assertEqual(group_vote["Choix 1"], 34.62)
        self.assertEqual(group_vote["Choix 2"], 65.38)
        group_vote = self.question2.get_results()
        self.assertEqual(group_vote["Choix 1"], 11.54)
        self.assertEqual(group_vote["Choix 2"], 88.46)

    def test_get_chart_results(self):
        data = self.question1.get_chart_results()
        self.assertEqual(data["chart_data"]["labels"], ["Choix 1", "Choix 2"])
        self.assertEqual(data["chart_data"]["values"], [30, 70])


class TestModelEventGroup(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            current=True,
            company=self.company,
        )
        self.group = EventGroup.objects.create(group_name="Groupe 1", weight=33)
        self.event.groups.add(self.group)
        self.user_lambda = create_dummy_user(self.company, "lambda", group=self.group)
        self.user_alpha = create_dummy_user(self.company, "alpha")

    def test_user_in_event(self):
        user_in_evt = EventGroup.user_in_event(self.event.slug, self.user_lambda)
        self.assertEqual(user_in_evt, True)
        user_in_evt = EventGroup.user_in_event(self.event.slug, self.user_alpha)
        self.assertEqual(user_in_evt, False)


class TestModelUserVote(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            current=True,
            company=self.company,
        )
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )
        self.group = EventGroup.objects.create(group_name="Groupe 1")
        self.event.groups.add(self.group)
        self.user_lambda = create_dummy_user(self.company, "lambda", group=self.group)
        self.user_alpha = create_dummy_user(self.company, "alpha")
        self.choice1 = Choice.objects.create(
            event=self.event, choice_text="Choix 1", choice_no=1
        )
        self.choice2 = Choice.objects.create(
            event=self.event, choice_text="Choix 2", choice_no=2
        )

    def test_get_user_vote(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question1,
            has_voted=False,
            nb_user_votes=1,
        )
        UserVote.objects.create(
            event=self.event,
            user=self.user_alpha,
            question=self.question1,
            has_voted=True,
            nb_user_votes=0,
        )
        user_vote = UserVote.get_user_vote(self.event.slug, self.user_lambda, 1)
        self.assertEqual(user_vote.has_voted, False)
        user_vote = UserVote.get_user_vote(self.event.slug, self.user_alpha, 1)
        self.assertEqual(user_vote.has_voted, True)

    def test_init_uservotes(self):
        UserVote.init_uservotes(self.event)
        new_user_list = UserVote.objects.filter(question__event__slug=self.event.slug)
        self.assertEqual(len(new_user_list), 2)
        self.assertEqual(new_user_list[0].user.user.username, "lambda")
        self.assertEqual(new_user_list[0].question.question_text, "Question 1")
        self.assertEqual(new_user_list[1].question.question_text, "Question 2")

    def test_set_vote(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question1,
            has_voted=False,
            nb_user_votes=1,
        )
        Result.objects.create(
            event=self.event,
            eventgroup=self.group, question=self.question1, choice=self.choice1
        )
        user_vote = UserVote.set_vote(self.event.slug, self.user_lambda, 1, 1)
        self.assertEqual(user_vote.has_voted, True)
        self.assertEqual(user_vote.nb_user_votes, 0)


class TestModelResult(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            current=True,
            company=self.company,
        )
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )
        self.group = EventGroup.objects.create(group_name="Groupe 1")
        self.event.groups.add(self.group)
        self.user_lambda = create_dummy_user(self.company, "lambda", group=self.group)
        self.user_alpha = create_dummy_user(self.company, "alpha")
        self.choice1 = Choice.objects.create(
            event=self.event, choice_text="Choix 1", choice_no=1
        )
        self.choice2 = Choice.objects.create(
            event=self.event, choice_text="Choix 2", choice_no=2
        )
        self.r1 = Result.objects.create(
            event=self.event,
            eventgroup=self.group, question=self.question1, choice=self.choice1
        )
        self.r2 = Result.objects.create(
            event=self.event,
            eventgroup=self.group, question=self.question1, choice=self.choice2
        )
        self.r3 = Result.objects.create(
            event=self.event,
            eventgroup=self.group, question=self.question2, choice=self.choice1
        )
        self.r4 = Result.objects.create(
            event=self.event,
            eventgroup=self.group, question=self.question2, choice=self.choice2
        )

    def test_add_vote(self):
        Result.add_vote(self.user_lambda, self.event.slug, 1, 1)
        self.r1.refresh_from_db()
        self.r2.refresh_from_db()
        self.r3.refresh_from_db()
        self.r3.refresh_from_db()
        self.assertEqual(self.r1.votes, 1)
        self.assertEqual(self.r2.votes, 0)
        self.assertEqual(self.r3.votes, 0)

    def test_get_vote_list(self):
        vote_list = Result.get_vote_list(self.event, self.group, 1)
        self.assertQuerysetEqual(
            vote_list,
            [
                "<Result: Votes du groupe Groupe 1 pour le choix 1 de la question 1>",
                "<Result: Votes du groupe Groupe 1 pour le choix 2 de la question 1>",
            ],
        )


class TestModelProcuration(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        self.group1 = EventGroup.objects.create(group_name="Groupe 1", weight=30)
        self.group2 = EventGroup.objects.create(group_name="Groupe 2", weight=70)
        self.event.groups.add(self.group1, self.group2)
        self.usr11 = create_dummy_user(self.company, "user11", self.group1)
        self.usr12 = create_dummy_user(self.company, "user12", self.group1)
        self.usr13 = create_dummy_user(self.company, "user13", self.group1)
        self.usr14 = create_dummy_user(self.company, "user14", self.group1)
        self.usr21 = create_dummy_user(self.company, "user21", self.group2)
        self.usr22 = create_dummy_user(self.company, "user22", self.group2)

    def test_get_proxy_status_no_proxy(self):
        proxy_list, user_proxy, user_proxy_list = Procuration.get_proxy_status(
            self.event.slug, self.usr11
        )
        self.assertEqual(len(proxy_list), 3)
        self.assertEqual(user_proxy, None)
        self.assertEqual(len(user_proxy_list), 0)

    def test_set_user_proxy(self):
        Procuration.set_user_proxy(self.event, self.usr11, self.usr13)
        proc = Procuration.objects.get(event=self.event, user=self.usr11)
        self.assertEqual(proc.user, self.usr11)
        self.assertEqual(proc.proxy, self.usr13)

    def test_confirm_proxy(self):
        Procuration.set_user_proxy(self.event, self.usr11, self.usr13)
        proc = Procuration.objects.get(event=self.event, user=self.usr11)
        self.assertEqual(proc.proxy_confirmed, False)
        Procuration.confirm_proxy(self.event, self.usr13, self.usr11.id)
        proc.refresh_from_db()
        self.assertEqual(proc.proxy_confirmed, True)

    def test_refuse_proxy(self):
        Procuration.set_user_proxy(self.event, self.usr11, self.usr13)
        proxy_list = Procuration.objects.filter(event=self.event)
        self.assertEqual(len(proxy_list), 1)
        Procuration.cancel_proxy(self.event.slug, self.usr11)
        proxy_list = Procuration.objects.filter(event=self.event)
        self.assertEqual(len(proxy_list), 0)


# ===================================
#            Test views
# ===================================


class TestLoginUser(TestCase):
    def test_login(self):
        self.company = create_dummy_company("Société de test")
        create_dummy_user(self.company, "toto")
        response = self.client.post(
            reverse("polls:login"), {"username": "toto", "password": "toto"}
        )
        logged_user = User.objects.get(username="toto")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(logged_user.is_authenticated, True)

    def test_login_unknown_user(self):
        response = self.client.post(
            reverse("polls:login"), {"username": "toto", "password": "toto"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error"], True)
        self.assertContains(response, "Utilisateur inconnu")

    def test_already_logged_in(self):
        self.company = create_dummy_company("Société de test")
        user = create_dummy_user(self.company, "toto")
        self.client.force_login(user.user)
        response = self.client.get(reverse("polls:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vous êtes déjà connecté")
        self.assertContains(response, user.user.username)


class TestIndex(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = create_dummy_company("Société de test")
        passed_date = timezone.now() - datetime.timedelta(days=1)
        future_date = timezone.now() + datetime.timedelta(days=1)
        Event.objects.create(
            event_name="Evénement passé",
            event_date=passed_date,
            slug=slugify("Evénement passé" + str(passed_date)),
            company=cls.company,
        )
        Event.objects.create(
            event_name="Evénement futur",
            event_date=future_date,
            slug=slugify("Evénement futur" + str(future_date)),
            company=cls.company,
        )

    def test_display_home_no_login_user(self):
        # Displays dedicated home page
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        # TO DO : Change next tests according to finalize home page
        # self.assertIn("login", response.url)

    def test_display_home(self):
        # Display only future events
        user = create_dummy_user(self.company, "toto")
        self.client.force_login(user.user)

        # Test with follow=True arg to be able to test htmlo content
        # Thus, status code will be 200 instead of 302 for a redirection
        response = self.client.get(reverse("polls:index"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prochain")
        self.assertContains(response, "Prévu le")
        self.assertNotContains(response, "Aucun")


class TestEvent(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        self.user_staff = create_dummy_user(self.company, "staff", staff=True)
        self.user_lambda = create_dummy_user(self.company, "lambda")
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

    def test_user_staff_event_not_started(self):
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

    def test_user_staff_event_started(self):
        self.client.force_login(self.user_staff.user)
        self.event.current = True
        self.event.save()
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertContains(response, "Accéder à l'événement")

    def test_user_lambda_event_not_started(self):
        self.group = EventGroup.objects.create(group_name="Groupe 1", weight=70)
        self.event.groups.add(self.group)
        self.group.users.add(self.user_lambda)
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertEqual(response.context["user_can_vote"], True)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

    def test_user_lambda_event_started(self):
        self.group = EventGroup.objects.create(group_name="Groupe 1", weight=70)
        self.event.groups.add(self.group)
        self.group.users.add(self.user_lambda)
        self.client.force_login(self.user_lambda.user)
        self.event.current = True
        self.event.save()
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertEqual(response.context["user_can_vote"], True)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertContains(response, "Accéder à l'événement")

    def test_user_lambda_not_in_event_list(self):
        self.client.force_login(self.user_lambda.user)
        self.event.current = True
        self.event.save()
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertEqual(response.context["user_can_vote"], False)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")


class TestQuestion(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        self.group = EventGroup.objects.create(group_name="Groupe 1", weight=70)
        self.event.groups.add(self.group)
        self.user_staff = create_dummy_user(self.company, "staff", group=self.group, staff=True)
        self.user_lambda = create_dummy_user(self.company, "lambda", group=self.group)
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )

    def test_launch_event_total_weight_not_100(self):
        # Launching event not possible until total groups' weight == 100
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_launch_event(self):
        # Add a group to have a total weight of 100
        group2 = EventGroup.objects.create(group_name="Groupe 2", weight=30)
        self.event.groups.add(group2)
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        my_event = get_object_or_404(Event, id=self.event.id)
        self.assertEqual(my_event.current, True)
        user_list = get_list_or_404(UserVote)
        self.assertEqual(len(user_list), 4)
        self.assertEqual(response.context["question_no"], 1)
        self.assertEqual(response.context["event"].current, True)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_first_question(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question1,
            has_voted=False,
            nb_user_votes=1,
        )
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_no"], 1)
        self.assertEqual(response.context["last_question"], False)
        self.assertEqual(response.context["user_vote"].has_voted, False)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Voter")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_question_user_has_voted(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question1,
            has_voted=True,
            nb_user_votes=0,
        )
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_no"], 1)
        self.assertEqual(response.context["event"].current, True)
        self.assertEqual(response.context["last_question"], False)
        self.assertEqual(response.context["user_vote"].has_voted, True)

    def test_user_display_last_question(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question2,
            has_voted=False,
            nb_user_votes=1,
        )
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 2))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_no"], 2)
        self.assertEqual(response.context["last_question"], True)
        self.assertContains(response, "Question 2")
        self.assertContains(response, "Voter")
        self.assertNotContains(response, "Résolution suivante")
