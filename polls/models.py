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
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    slug = models.SlugField(unique=True)
    current = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

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
    question_text = models.CharField(max_length=200)
    question_no = models.IntegerField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Question"

    def __str__(self):
        return self.question_text
    
    @classmethod
    def get_question_list(cls, event_slug):
        return cls.objects.filter(event__slug=event_slug)

    @classmethod
    def get_question(cls, event_slug, question_no):
        return cls.objects.get(event__slug=event_slug, question_no=question_no)


class Choice(models.Model):
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"

    def __str__(self):
        return self.choice_text

    @classmethod
    def get_choice_list(cls, event_slug, question_no):
        return Choice.objects.filter(question__event__slug=event_slug,
            question__question_no=question_no)

    @classmethod
    def add_vote(cls, id):
        choice = cls.objects.get(id=id)
        choice.votes += 1
        choice.save()


class EventGroup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    # group = models.ForeignKey(Group, on_delete=models.CASCADE)   # - Prévoir relation  ManyToMany
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Evénements : groupes d'utilisateurs"
        verbose_name_plural = "Evénements : groupes d'utilisateurs"

    def __str__(self):
        return "Groupes associés à l'événement " + self.event.event_name

    @classmethod
    def count_total_votes(cls, event_slug):
        # Returns the number of users supposed to vote for the related event
        return cls.objects.filter(event__slug=event_slug).aggregate(Count('user'))['user__count']

    @classmethod
    def user_in_event_group(cls, event_slug, user):
        user_in_group = False
        if len(cls.objects.filter(event__slug=event_slug, user=user)) > 0:
            user_in_group = True
        return user_in_group


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
        return "Vote de " + self.user.username + " à la question " + self.question.question_text

    @classmethod
    def get_user_vote(cls, user, question_no):
        return cls.objects.get(user=user, question__question_no=question_no)

    @classmethod
    def init_uservotes(cls, event_slug):
        event_user_list = get_list_or_404(EventGroup, event__slug=event_slug)
        question_list = get_list_or_404(Question, event__slug=event_slug)
        for event_user in event_user_list:
            for question in question_list:
                cls.objects.create(user=event_user.user, question=question)

    
    @classmethod
    def set_vote(cls, question_no, user):
        # Filter to get a list to be able to use update method
        user_vote = cls.objects.filter(question__question_no=question_no, user=user)
        user_vote.update(has_voted=True, date_vote=timezone.now())
        # Only one lement is in the list : save the update and return the single element
        user_vote[0].save()
        return user_vote[0]