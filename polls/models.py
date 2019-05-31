# -*-coding:Utf-8 -*

from django.db import models
from django.contrib.auth.models import User, Group
from django.shortcuts import get_list_or_404, get_object_or_404
from django.utils import timezone
from django.db.models import Count



class Company(models.Model):
    company_name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="img/", null=True)

    class Meta:
        verbose_name = "Société"

    def __str__(self):
        return self.company_name

    @classmethod
    def get_company(cls, id):
        return cls.objects.get(id=id)


class Event(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    rules = [
        ('MAJ', 'Majorité'),
        ('PROP', 'Proportionnelle')
    ]
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    slug = models.SlugField(unique=True)
    current = models.BooleanField(default=False)
    quorum = models.IntegerField(default=33)
    rule = models.CharField(max_length=5, choices=rules, default='MAJ')

    class Meta:
        verbose_name = "Evénement"

    def __str__(self):
        return self.event_name

    @classmethod
    def get_event(cls, event_slug):
        return get_object_or_404(Event, slug=event_slug)

    @classmethod
    def get_next_events(cls, company):
        return cls.objects.filter(company=company, event_date__gte=timezone.now())

    def set_current(self):
        self.current = True
        self.save()


class Question(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=200)
    question_no = models.IntegerField()

    class Meta:
        verbose_name = "Question"

    def __str__(self):
        return self.question_text
    
    @classmethod
    def get_question_list(cls, event_slug):
        return cls.objects.filter(event__slug=event_slug).order_by('question_no')

    @classmethod
    def get_question(cls, event_slug, question_no):
        return cls.objects.get(event__slug=event_slug, question_no=question_no)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    choice_no = models.IntegerField()
    votes = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"

    def __str__(self):
        return self.choice_text

    @classmethod
    def get_choice_list(cls, event_slug, question_no):
        return Choice.objects.filter(question__event__slug=event_slug,
            question__question_no=question_no).order_by('choice_no')


class EventGroup(models.Model):
    evt_group = models.ForeignKey(Group, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    vote_weight = models.IntegerField(default=0)
    
    def __str__(self):
        return self.evt_group.name

    class Meta:
        verbose_name = "Groupe d'utilisateurs"
        verbose_name_plural = "Groupes d'utilisateurs"

    @classmethod
    def get_list(cls, event_slug):
        return cls.objects.filter(event__slug=event_slug)

    # @classmethod
    # def count_total_votes(self):
        # ===============================================
        # A MODIFIER POUR PRENDRE EN COMPTE LES GROUPES ?
        # ===============================================
        # Returns the number of users supposed to vote for the related event
        # return self.objects.filter(event__slug=event_slug).aggregate(Count('user'))['user__count']


class UserVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    proxy_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='proxy')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)
    date_vote = models.DateTimeField(null=True)

    class Meta:
        verbose_name = "Vote utilisateurs et pouvoirs"
        verbose_name_plural = "Votes utilisateurs et pouvoirs"

    def __str__(self):
        return "Vote de " + self.user.username

    @classmethod
    def get_user_vote(cls, event_slug, user, question_no):
        return cls.objects.get(user=user, question__event__slug=event_slug, question__question_no=question_no)

    @classmethod
    def init_uservotes(cls, event_slug):
        event_user_list = [user for user in User.objects.filter(groups__eventgroup__event__slug=event_slug)]
        question_list = Question.get_question_list(event_slug)
        user_group_list = EventGroup.objects.filter(event__slug=event_slug)
        for question in question_list:
            for event_user in event_user_list:
                cls.objects.create(user=event_user, question=question)
            choice_list = Choice.get_choice_list(event_slug, question.question_no)
            for choice in choice_list:
                for usr_group in user_group_list:
                    GroupVote.objects.create(eventgroup=usr_group, choice=choice)

    @classmethod
    def user_in_event(cls, event_slug, user):
        user_in_group = False
        if len(cls.objects.filter(user__groups__eventgroup__event__slug=event_slug, user=user)) > 0:
            user_in_group = True
        return user_in_group

    @classmethod
    def set_vote(cls, event_slug, user, question_no, choice_id):
        user_vote = cls.get_user_vote(event_slug, user, question_no)
        user_vote.has_voted, user_vote.date_vote = True, timezone.now()
        user_vote.save()
        GroupVote.add_vote(user, choice_id)
        return user_vote

class GroupVote(models.Model):
    eventgroup = models.ForeignKey(EventGroup, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    votes = models.IntegerField(default=0)
    
    def __str__(self):
        return "Votes du groupe " + self.eventgroup.evt_group.name + " pour le choix " + str(self.choice.choice_no) + " de la question " + str(self.choice.question.question_no)

    class Meta:
        verbose_name = 'GroupVote'
        verbose_name_plural = 'GroupVotes'

    @classmethod
    def add_vote(cls, user, choice_id):
        group_choice = cls.objects.get(eventgroup__evt_group__user=user, choice__id=choice_id)
        group_choice.votes += 1
        group_choice.save()
    
    @classmethod
    def get_vote_list(cls, evt_group, question_no):
        return cls.objects.filter(eventgroup=evt_group,
            choice__question__question_no=question_no).order_by('choice__choice_no')

