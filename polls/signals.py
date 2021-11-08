# -*-coding:Utf-8 -*

from .models import Company, UserGroup, UserComp
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create a default hidden group when a new company is created
@receiver(post_save, sender=Company)
def create_default_group(sender, instance, created, **kwargs):
    if created:
        UserGroup.create_group(
            {
                "company": instance,
                "group_name": "Default Group",
                "weight": 100,
                "hidden": True
            }
        )

# Each new user is added to the company's default hidden group
@receiver(post_save, sender=UserComp)
def add_to_default_group(sender, instance, created, **kwargs):
    if created:
        def_group = instance.company.get_default_group()
        def_group.users.add(instance)
