# -*-coding:Utf-8 -*

from django.contrib import admin

from .models import Company, Event, Question, Choice, UserVote, EventGroup, GroupVote

class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug" : ("event_name", "event_date")}


admin.site.register(Company)
admin.site.register(Event, EventAdmin)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(UserVote)
admin.site.register(EventGroup)
admin.site.register(GroupVote)

