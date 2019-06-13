# -*-coding:Utf-8 -*

from django.db import models
from django.contrib.auth.models import User, Group
from django.shortcuts import get_list_or_404, get_object_or_404
from django.utils import timezone
from django.db.models import Count, UniqueConstraint
from django.conf import settings


class Company(models.Model):
    # A COMPLETER : AJOUT INFOS LEGALES (adresse, SIRET, etc.)
    company_name = models.CharField("nom", max_length=200)
    logo = models.ImageField(upload_to="img/", null=True, blank=True)
    statut = models.CharField("forme juridique", max_length=50)
    siret = models.CharField("SIRET", max_length=50)
    street_num = models.IntegerField("N° de rue", null=True, blank=True)
    street_cplt = models.CharField("complément", max_length=50, null=True, blank=True)
    address1 = models.CharField("adresse", max_length=300)
    address2 = models.CharField("complément d'adresse", max_length=300, null=True, blank=True)
    zip_code = models.IntegerField("code postal")
    city = models.CharField("ville", max_length=200)
    host = models.CharField("serveur mail", max_length=50, null=True, blank=True)
    port = models.IntegerField("port du serveur", null=True, blank=True)
    hname = models.EmailField("utilisateur", max_length=100, null=True, blank=True)
    fax = models.CharField("mot de passe", max_length=50, null=True, blank=True)
    use_tls = models.BooleanField("authentification requise", default=True, blank=True)
    

    class Meta:
        verbose_name = "Société"

    def __str__(self):
        return self.company_name

    @classmethod
    def get_company(cls, id):
        return cls.objects.get(id=id)


class EventGroup(models.Model):
    # PREVOIR METHODE "on update" POUR METTRE A JOUR LE POIDS DANS USERGROUP POUR LES EVTS FUTURS SI CHGT DU POIDS
    users = models.ManyToManyField(User, verbose_name="utilisateurs")
    group_name = models.CharField("nom", max_length=100)
    weight = models.IntegerField("poids", default=0)
    
    def __str__(self):
        return self.group_name

    class Meta:
        verbose_name = "Groupe d'utilisateurs"
        verbose_name_plural = "Groupes d'utilisateurs"

    @classmethod
    def get_list(cls, event_slug):
        return cls.objects.filter(event__slug=event_slug)

    @classmethod
    def user_in_event(cls, event_slug, user):
        user_in_group = False
        if len(user.eventgroup_set.filter(event__slug=event_slug)) > 0:
            user_in_group = True
        return user_in_group

    @classmethod
    def get_proxy_list(cls, event_slug, user):
        # A REVOIR ET CORRIGER
        group = user.eventgroup_set.all()
        proxy_users = Procuration.objects.all()
        user_list = group.users.exclude(user=user)
        group_list = cls.objects.filter(event__slug=event_slug)
        # cls.objects.filter(user__groups__eventgroup__evt_group__user=user, proxy_user__isnull=True).exclude(user=user).values('user').distinct()



class Event(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    groups = models.ManyToManyField(EventGroup, verbose_name="groupes")
    rules = [
        ('MAJ', 'Majorité'),
        ('PROP', 'Proportionnelle')
    ]
    event_name = models.CharField("nom", max_length=200)
    event_date = models.DateField("date de l'événement")
    slug = models.SlugField(unique=True)
    current = models.BooleanField("en cours", default=False)
    quorum = models.IntegerField(default=33)
    rule = models.CharField("mode de scrutin", max_length=5, choices=rules, default='MAJ')

    class Meta:
        verbose_name = "Evénement"
        UniqueConstraint(fields=['company__id', 'slug'], name='unique_slug')

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
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="événement")
    question_text = models.TextField("texte de la résolution")
    question_no = models.IntegerField("numéro de résolution")

    class Meta:
        verbose_name = "Résolution"

    def __str__(self):
        return self.question_text
    
    @classmethod
    def get_question_list(cls, event_slug):
        return cls.objects.filter(event__slug=event_slug).order_by('question_no')

    @classmethod
    def get_question(cls, event_slug, question_no):
        return cls.objects.get(event__slug=event_slug, question_no=question_no)

    def get_results(self):
        # Calcultate global results for the question
        evt_group_list = EventGroup.get_list(self.event.slug)

        # Initialize global results data
        global_choice_list = Choice.get_choice_list(self.event.slug).values('choice_text', 'votes')
        group_vote = {}
        # global_total_votes = 0
        # global_nb_votes = 0
        for choice in global_choice_list:
            group_vote[choice['choice_text']] = 0

        # Gather votes info for each group
        for evt_group in evt_group_list:
            total_votes = EventGroup.objects.filter(id=evt_group.id).aggregate(Count('users'))['users__count']
        
            choice_list = Result.get_vote_list(evt_group, self.question_no).values('choice__choice_text', 'votes', 'group_weight')

            labels = [choice['choice__choice_text'] for choice in choice_list]
            values = [choice['votes'] for choice in choice_list]

            # Calculate aggregate results
            weight = choice_list[0]['group_weight']
            if self.event.rule == 'MAJ':
                max_val = values.index(max(values))
                group_vote[labels[max_val]] += weight           # A MODIFIER : cas d'égalité, cas où pas de valeur
            elif self.event.rule == 'PROP':
                for i, choice in enumerate(labels):
                    group_vote[choice] += values[i] * weight / 100

        return group_vote

    def get_chart_results(self):
        group_vote = self.get_results()

        # Setup global info for charts
        global_labels = []
        global_values = []
        for label, value in group_vote.items():
            global_labels.append(label)
            global_values.append(value)

        nb_votes = sum(global_values)

        group_data = {
            'labels': global_labels,
            'values': global_values,
            }

        chart_background_colors = settings.BACKGROUND_COLORS
        chart_border_colors = settings.BORDER_COLORS

        # Extends color lists to fit with nb values to display
        while len(chart_background_colors) < nb_votes:
            chart_background_colors += settings.BACKGROUND_COLORS
            chart_border_colors += settings.BACKGROUND_COLORS

        data = {
            'chart_data': group_data,
            'backgroundColor': chart_background_colors,
            'borderColor': chart_border_colors,
            }

        return data

class Choice(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, verbose_name="événement")
    choice_text = models.CharField("libellé", max_length=200)
    choice_no = models.IntegerField("numéro de question")
    votes = models.IntegerField("nombre de votes", default=0)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"

    def __str__(self):
        return self.choice_text

    @classmethod
    def get_choice_list(cls, event_slug):
        return Choice.objects.filter(event__slug=event_slug).order_by('choice_no')


class UserVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="utilisateur")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="résolution")
    nb_user_votes = models.IntegerField()
    has_voted = models.BooleanField("a voté", default=False)
    date_vote = models.DateTimeField("date du vote", null=True)

    class Meta:
        verbose_name = "Vote utilisateurs et pouvoirs"
        verbose_name_plural = "Votes utilisateurs et pouvoirs"

    def __str__(self):
        return "Vote de " + self.user.username + " pour la question n° " + str(self.question.question_no)

    @classmethod
    def get_user_vote(cls, event_slug, user, question_no):
        return cls.objects.get(user=user, question__event__slug=event_slug, question__question_no=question_no)

    @classmethod
    def init_uservotes(cls, event):
        event_user_list = [user for user in User.objects.filter(eventgroup__event=event)]
        question_list = Question.get_question_list(event.slug)
        user_group_list = EventGroup.objects.filter(event=event)
        event_choice_list = Choice.get_choice_list(event.slug)
        for question in question_list:
            for event_user in event_user_list:
                nb_user_votes = 1
                proxy_list, user_proxy, user_proxy_list = Procuration.get_proxy_status(event.slug, event_user)
                if user_proxy:
                    nb_user_votes = 0
                elif user_proxy_list:
                    nb_user_votes += len(user_proxy_list)
                cls.objects.create(user=event_user, question=question, nb_user_votes=nb_user_votes)
            for event_choice in event_choice_list:
                for usr_group in user_group_list:
                    Result.objects.create(eventgroup=usr_group, choice=event_choice, question=question, group_weight=usr_group.weight)

    @classmethod
    def set_vote(cls, event_slug, user, question_no, choice_id):
        user_vote = cls.get_user_vote(event_slug, user, question_no)
        user_vote.nb_user_votes, user_vote.has_voted, user_vote.date_vote = user_vote.nb_user_votes - 1, True, timezone.now()
        user_vote.save()
        Result.add_vote(user, question_no, choice_id)
        return user_vote


class Result(models.Model):
    # ENVISAGER CHANGEMENT DE NOM ( => Results ?)
    eventgroup = models.ForeignKey(EventGroup, on_delete=models.CASCADE, verbose_name="groupe d'utilisateurs")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, verbose_name="choix")
    votes = models.IntegerField("nombre de votes", default=0)
    group_weight = models.IntegerField("poids", default=0)
    
    def __str__(self):
        return "Votes du groupe " + self.eventgroup.group_name + " pour le choix " + str(self.choice.choice_no) + " de la question " + str(self.question.question_no)

    class Meta:
        verbose_name = "Résultat des votes"
        verbose_name_plural = "Résultats des votes"

    @classmethod
    def add_vote(cls, user, question_no, choice_id):
        group_choice = cls.objects.get(eventgroup__users=user, question__question_no=question_no, choice__id=choice_id)
        group_choice.votes += 1
        group_choice.save()

    
    @classmethod
    def get_vote_list(cls, evt_group, question_no):
        return cls.objects.filter(eventgroup=evt_group,
            question__question_no=question_no).order_by('choice__choice_no')


class Procuration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="utilisateur")
    proxy = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proxy', verbose_name="récipiendaire")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="événement")
    proxy_date = models.DateField("date de procuration")
    proxy_confirmed = models.BooleanField("procuration confirmée", default=False)
    confirm_date = models.DateField("date de confirmation", null=True, blank=True)

    def __str__(self):
        return "Procuration de " + self.user.last_name + " pour l'événement " + self.event.event_name

    class Meta:
        verbose_name = 'Procuration'

    @classmethod
    def get_proxy_status(cls, event_slug, user):
        user_proxy_list = []
        proxy_list = []
        user_proxy = None
        if len(cls.objects.filter(proxy=user, event__slug=event_slug)) > 0:
            # Case user is proxyholder => get proxy list
            user_proxy_list = cls.objects.filter(proxy=user, event__slug=event_slug).order_by('user__last_name')
        elif len(cls.objects.filter(user=user)) > 0:
            # Case user has given proxy => get proxyholder
            usv = cls.objects.get(user=user)
            user_proxy = User.objects.get(id=usv.proxy.id)
        else:
            # Case user has no proxy and is not proxyholder => get list of users that could receive his proxy
            # Get list of users from the same group, except the user hiself and those who already gave proxy
            # As values are restricted to user_id, we need to transform them into a list usable in the next request
            id_list = [int(proxy['user__id']) for proxy in cls.objects.all().values('user__id')]
            proxy_list = User.objects.filter(eventgroup__users=user).exclude(id=user.id).exclude(id__in=id_list).order_by('last_name')
        return proxy_list, user_proxy, user_proxy_list

    @classmethod
    def set_user_proxy(cls, event, user, proxy):
        cls.objects.create(event=event, user=user, proxy=proxy, proxy_date=timezone.now())


    @classmethod
    def confirm_proxy(cls, event, user, proxy_id):
        proc = cls.objects.get(user__id=proxy_id, proxy=user, event=event)
        if not proc.proxy_confirmed:
            proc.proxy_confirmed, proc.confirm_date = True, timezone.now()
            proc.save()


    @classmethod
    def cancel_proxy(cls, event_slug, user, *args):
        if len(args) == 1:
            cls.objects.filter(event__slug=event_slug, user__id=user, proxy=args[0]).delete()
        else:
            cls.objects.filter(event__slug=event_slug, user=user).delete()
