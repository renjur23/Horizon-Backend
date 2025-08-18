# authentication/management/commands/test_email.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tests email sending functionality'

    def handle(self, *args, **options):
        logger.info("Testing email configuration...")
        logger.info(f"Using email: {settings.EMAIL_HOST_USER}")
        
        try:
            send_mail(
                'Email Configuration Test',
                'This is a test email from your Django app',
                settings.EMAIL_HOST_USER,
                ['recipient@example.com'],  # Change to your email
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('Email sent successfully!'))
        except Exception as e:
            logger.error(f"Email failed: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Email failed: {str(e)}'))