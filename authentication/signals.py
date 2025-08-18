from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser
import random

@receiver(post_save, sender=CustomUser)
def send_activation_email(sender, instance, created, **kwargs):
    if created:
        otp = str(random.randint(1000, 99999))
        CustomUser.objects.filter(pk=instance.pk).update(otp=otp)

        subject = 'Verify Your Email'
        message = f'Your OTP for registration is: {otp}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email], fail_silently=False)
