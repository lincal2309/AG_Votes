# -*-coding:Utf-8 -*

from django.contrib import admin

from .models import Company, Event, Question, Choice, UserVote, EventGroup, Result, Procuration

class PollsAdminSite(admin.AdminSite):
    site_header = 'Administration de l\'application Votes'

admin_site = PollsAdminSite(name='polls_admin')



class CompanyAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['company_name', 'logo']}),
        ('Informations administratives', {'fields': ['statut', 'siret', 'street_num', 'street_cplt', 'address1', 'address2', 'zip_code', 'city']}),
        ('Configuration de la messagerie', {'fields': ['host', 'port', 'hname', 'fax', 'use_tls'], 'classes': ['collapse']}),
    ]


class ChoiceInLine(admin.TabularInline):
    model = Choice
    fields = ['choice_text', 'choice_no']
    extra = 3


class QuestionInLine(admin.TabularInline):
    model = Question
    fields = ['question_text', 'question_no']
    extra = 3



class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug" : ("event_name", "event_date")}
    fields = ['event_name', 'event_date', 'slug', 'groups', 'quorum', 'rule', 'current']
    list_display = ('event_name', 'event_date', 'quorum', 'rule', 'current')
    ordering = ('event_date', 'event_name')
    filter_horizontal = ('groups',)
    inlines = [QuestionInLine, ChoiceInLine]

class EventGroupAdmin(admin.ModelAdmin):
    fields = ['group_name', 'weight', 'users']
    filter_horizontal = ('users',)
    

class UserVoteAdmin(admin.ModelAdmin):
    list_display = ('uservote_label', 'has_voted', 'date_vote')

    def uservote_label(self, obj):
        return "Vote de %s pour la question n° %s" % (obj.user.username, str(obj.question.question_no))
    uservote_label.short_description = "Vote utilisateur"

class ResultAdmin(admin.ModelAdmin):
    list_display = ('eventgroup', 'question', 'choice', 'votes')
    ordering = ('eventgroup', 'question', 'choice')

class ProcurationAdmin(admin.ModelAdmin):
    list_display = ('procuration_detail', 'utilisateur_id', 'recipiendaire_id')

    def procuration_detail(self, obj):
        return "Procuration de %s pour l'événement %s" % (obj.user.last_name, obj.event.event_name)
    procuration_detail.short_description = "Procuration"

    def utilisateur_id(self, obj):
        return obj.user.id

    def recipiendaire_id(self, obj):
        return obj.proxy.id



admin.site.register(Company, CompanyAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(UserVote, UserVoteAdmin)
admin.site.register(EventGroup, EventGroupAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Procuration, ProcurationAdmin)
