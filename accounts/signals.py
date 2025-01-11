from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User, UserBalance


@receiver(post_save, sender=User)
def create_user_balance(sender, instance: User, created, **kwargs):
    if created:
        UserBalance.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_user_referral_code(sender, instance: User, created, **kwargs):
    if created:
        instance.referral_code = instance.generate_referral_code()
        instance.save()
