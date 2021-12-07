# -*-coding:Utf-8 -*

from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import reverse, get_list_or_404, get_object_or_404
from django.contrib.auth.models import User

import datetime

from .tools_tests import (
    create_dummy_user,
    create_dummy_company,
    create_dummy_event,
    set_default_context,
    set_full_context
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

# ===================================
#        Test models' methods
# ===================================


class TestModelCompany(TestCase):
    def test_create_company(self):
        comp = create_dummy_company("Société de test")
        default_group = comp.get_default_group()
        self.assertEqual(default_group.id, 1)
        self.assertEqual(default_group.hidden, True)


    def test_get_company(self):
        comp = create_dummy_company("Société de test")
        company = Company.get_company("societe-de-test")
        self.assertEqual(comp.id, company.id)


class TestModelEvent(TestCase):
    def test_get_event(self):
        self.company = create_dummy_company("Société de test")
        event_start_date = datetime.date(2150, 5, 12)
        self.event = create_dummy_event(
            self.company,
            name = "Evénement de test",
            event_start_date = event_start_date
        )
        my_event = Event.get_event(self.company.comp_slug, "evenement-de-test2150-05-12")
        self.assertEqual(self.event, my_event)

    def test_get_next_events(self):
        company = create_dummy_company("Société de test")

        passed_date = timezone.now() - datetime.timedelta(days=1)
        Event.create_event(company, "Evénement passé", passed_date)
        create_dummy_event(company, name = "Evénement futur")

        next_events = Event.get_next_events(company)
        self.assertEqual(len(next_events), 1)
        self.assertEqual(next_events[0].event_name, "Evénement futur")

    def test_set_current(self):
        self.company = create_dummy_company("Société de test")
        event_start_date = datetime.date(2150, 5, 12)
        self.event = Event.create_event(
            self.company,
            "Evénement de test",
            event_start_date,
        )

        self.assertEqual(self.event.current, False)
        self.event.set_current()
        self.assertEqual(self.event.current, True)


class TestModelQuestion(TestCase):
    def setUp(self):
        self.test_data = set_full_context()
 
    def test_create_question(self):
        question = Question.create_question(self.test_data["event1"], 3, "Question 3")
        # 3 events created, 2 questions per event => this question is the 7th
        self.assertEqual(question.id, 7)

    def test_get_question_list(self):
        question_list = Question.get_question_list(self.test_data["event1"])
        self.assertEqual(len(question_list), 2)
        self.assertEqual(question_list[0].question_text, "Question 1")
        self.assertEqual(question_list[1].question_text, "Question 2")

    def test_get_question(self):
        my_question = Question.get_question(self.test_data["event1"], 1)
        self.assertEqual(my_question, self.test_data["question_list_1"][0])

    def test_get_results_maj(self):
        group_vote = self.test_data["question_list_1"][0].get_results()
        self.assertEqual(group_vote["Choix 1"], 30)
        self.assertEqual(group_vote["Choix 2"], 70)
        group_vote = self.test_data["question_list_1"][1].get_results()
        self.assertEqual(group_vote["Choix 1"], 0)
        self.assertEqual(group_vote["Choix 2"], 100)

    def test_get_results_prop(self):
        Event.objects.filter(id=self.test_data["event1"].id).update(rule="PROP")
        self.test_data["event1"].refresh_from_db()
        group_vote = self.test_data["question_list_1"][0].get_results()
        self.assertEqual(group_vote["Choix 1"], 34.62)
        self.assertEqual(group_vote["Choix 2"], 65.38)
        group_vote = self.test_data["question_list_1"][1].get_results()
        self.assertEqual(group_vote["Choix 1"], 11.54)
        self.assertEqual(group_vote["Choix 2"], 88.46)

    def test_get_chart_results(self):
        data = self.test_data["question_list_1"][0].get_chart_results()
        self.assertEqual(data["chart_data"]["labels"], ["Choix 1", "Choix 2"])
        self.assertEqual(data["chart_data"]["values"], [30, 70])


class TestModelUserGroup(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")

        self.usr11 = create_dummy_user(self.company, "user11")
        self.usr12 = create_dummy_user(self.company, "user12", admin=True)
        self.usr13 = create_dummy_user(self.company, "user13")
        self.usr14 = create_dummy_user(self.company, "user14")
        self.usr21 = create_dummy_user(self.company, "user21")
        self.usr22 = create_dummy_user(self.company, "user22")

    def test_create_group(self):
        # Group with no users
        self.group0 = UserGroup.create_group(self.company, "Groupe sans users")

        self.assertEqual(self.group0.id, 2)
        g0_users = self.group0.users.all()
        self.assertEqual(len(g0_users), 0)
        self.assertEqual(self.group0.nb_users, 0)

        # Group with multiple users
        user_list = [self.usr11.id, self.usr12.id, self.usr13.id, self.usr14.id]
        users = UserComp.objects.filter(id__in=user_list)
        self.group1 = UserGroup.create_group(self.company, "Groupe 1", user_list=users)
        
        self.assertEqual(self.group1.id, 3)
        g1_users = self.group1.users.all()
        self.assertEqual(len(g1_users), 4)
        self.assertEqual(self.group1.nb_users, 4)
        self.assertIn(self.usr12, g1_users)

        # Group with 1 user
        self.group2 = UserGroup.create_group(self.company, "Groupe 2", user=self.usr11)

        self.assertEqual(self.group2.id, 4)
        self.assertEqual(self.group2.nb_users, 1)
        g2_users = self.group2.users.all()
        self.assertIn(self.usr11, g2_users)
        self.assertNotIn(self.usr22, g2_users)

        usr11_groups = self.usr11.usergroup_set.all()
        self.assertEqual(len(usr11_groups), 3)


    def test_user_in_event(self):
        self.group1 = UserGroup.create_group(self.company, "Groupe 1", user=self.usr11)
        self.event = create_dummy_event(
            self.company,
            name="Evénement de test",
            current=True,
            groups=[self.group1],
        )

        user_in_evt = UserGroup.user_in_event(self.event, self.usr11)
        self.assertEqual(user_in_evt, True)
        user_in_evt = UserGroup.user_in_event(self.event, self.usr12)
        self.assertEqual(user_in_evt, False)


class TestModelUserVote(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")

        self.group = UserGroup.create_group(self.company, "Groupe 1", weight=40)
        self.user_lambda = create_dummy_user(self.company, "lambda", group=self.group)
        self.user_alpha = create_dummy_user(self.company, "alpha")

        self.event = create_dummy_event(
            self.company,
            name="Evénement de test",
            current=True,
            groups=[self.group],
        )

        self.question_list = Question.get_question_list(self.event)
        self.choice_list = Choice.get_choice_list(self.event)

    def test_set_vote(self):
        UserVote.set_vote(self.event, self.user_lambda, self.question_list[0])

        Result.objects.create(
            event=self.event,
            usergroup=self.group, question=self.question_list[0], choice=self.choice_list[0]
        )
        user_vote = UserVote.set_vote(self.event, self.user_lambda, self.question_list[0], choices=[self.choice_list[0]])
        self.assertEqual(user_vote.has_voted, True)
        self.assertEqual(user_vote.nb_user_votes, 0)

    def test_get_user_vote(self):
        UserVote.set_vote(self.event, self.user_lambda, self.question_list[0])
        UserVote.set_vote(self.event, self.user_alpha, self.question_list[0], has_voted=True, nb_user_votes=0)

        user_vote = UserVote.get_user_vote(self.event, self.user_lambda, 1)
        self.assertEqual(user_vote.has_voted, False)
        user_vote = UserVote.get_user_vote(self.event, self.user_alpha, 1)
        self.assertEqual(user_vote.has_voted, True)

    def test_init_uservotes(self):
        UserVote.init_uservotes(self.event)
        new_user_list = UserVote.objects.filter(question__event=self.event)
        self.assertEqual(len(new_user_list), 2)
        self.assertEqual(new_user_list[0].user.user.username, "lambda")
        self.assertEqual(new_user_list[0].question.question_text, "Question 1")
        self.assertEqual(new_user_list[1].question.question_text, "Question 2")


class TestModelResult(TestCase):
    def setUp(self):
        self.test_data = set_default_context()

        self.r1 = Result.objects.create(
            event=self.test_data["event1"],
            usergroup=self.test_data["group1"],
            question=self.test_data["question_list_1"][0],
            choice=self.test_data["choice_list_1"][0]
        )
        self.r2 = Result.objects.create(
            event=self.test_data["event1"],
            usergroup=self.test_data["group1"],
            question=self.test_data["question_list_1"][0],
            choice=self.test_data["choice_list_1"][1]
        )
        self.r3 = Result.objects.create(
            event=self.test_data["event1"],
            usergroup=self.test_data["group1"],
            question=self.test_data["question_list_1"][1],
            choice=self.test_data["choice_list_1"][0]
        )
        self.r4 = Result.objects.create(
            event=self.test_data["event1"],
            usergroup=self.test_data["group1"],
            question=self.test_data["question_list_1"][1],
            choice=self.test_data["choice_list_1"][1]
        )

    def test_add_vote(self):
        Result.add_vote(self.test_data["usr11"],
            self.test_data["event1"],
            self.test_data["question_list_1"][0],
            [self.test_data["choice_list_1"][0]])
        self.r1.refresh_from_db()
        self.r2.refresh_from_db()
        self.r3.refresh_from_db()
        self.r3.refresh_from_db()
        self.assertEqual(self.r1.votes, 1)
        self.assertEqual(self.r2.votes, 0)
        self.assertEqual(self.r3.votes, 0)

    def test_get_vote_list(self):
        vote_list = Result.get_vote_list(
            self.test_data["event1"],
            self.test_data["group1"],
            self.test_data["question_list_1"][0])
        self.assertQuerysetEqual(
            vote_list,
            [
                "<Result: Votes du groupe Groupe 1 pour le choix 1 de la question 1>",
                "<Result: Votes du groupe Groupe 1 pour le choix 2 de la question 1>",
            ],
        )


class TestModelProcuration(TestCase):
    def setUp(self):
        self.test_data = set_default_context()

        # self.company = create_dummy_company("Société de test")
        # # event_start_date = timezone.now() + datetime.timedelta(days=1)
        # self.event = create_dummy_event(
        #     self.company,
        #     name="Evénement de test",
        # )
        # self.group1 = UserGroup.objects.create(group_name="Groupe 1", weight=30)
        # self.group2 = UserGroup.objects.create(group_name="Groupe 2", weight=70)
        # self.event.groups.add(self.group1, self.group2)
        # self.usr11 = create_dummy_user(self.company, "user11", self.group1)
        # self.usr12 = create_dummy_user(self.company, "user12", self.group1)
        # self.usr13 = create_dummy_user(self.company, "user13", self.group1)
        # self.usr14 = create_dummy_user(self.company, "user14", self.group1)
        # self.usr21 = create_dummy_user(self.company, "user21", self.group2)
        # self.usr22 = create_dummy_user(self.company, "user22", self.group2)

    def test_get_proxy_status_no_proxy(self):
        proxy_list, user_proxy, user_proxy_list = Procuration.get_proxy_status(
            self.test_data["event1"], self.test_data["usr11"]
        )
        print(proxy_list)
        self.assertEqual(len(proxy_list), 3)
        self.assertEqual(user_proxy, None)
        self.assertEqual(len(user_proxy_list), 0)

    def test_set_user_proxy(self):
        Procuration.set_user_proxy(self.test_data["event1"], self.test_data["usr11"], self.test_data["usr13"])
        proc = Procuration.objects.get(event=self.test_data["event1"], user=self.test_data["usr11"])
        self.assertEqual(proc.user, self.test_data["usr11"])
        self.assertEqual(proc.proxy, self.test_data["usr13"])

    def test_confirm_proxy(self):
        Procuration.set_user_proxy(self.test_data["event1"], self.test_data["usr11"], self.test_data["usr13"])
        proc = Procuration.objects.get(event=self.test_data["event1"], user=self.test_data["usr11"])
        self.assertEqual(proc.proxy_confirmed, False)
        Procuration.confirm_proxy(self.test_data["event1"], self.test_data["usr13"], self.test_data["usr11"].id)
        proc.refresh_from_db()
        self.assertEqual(proc.proxy_confirmed, True)

    def test_refuse_proxy(self):
        Procuration.set_user_proxy(self.test_data["event1"], self.test_data["usr11"], self.test_data["usr13"])
        proxy_list = Procuration.objects.filter(event=self.test_data["event1"])
        self.assertEqual(len(proxy_list), 1)
        Procuration.cancel_proxy(self.test_data["event1"], self.test_data["usr11"])
        proxy_list = Procuration.objects.filter(event=self.test_data["event1"])
        self.assertEqual(len(proxy_list), 0)
