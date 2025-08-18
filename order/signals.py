from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from order.models import Order
import logging

logger = logging.getLogger('django')

@receiver(post_save, sender=Order)
def send_po_created_or_hired_email(sender, instance, created, **kwargs):
    logger.info("📨 Signal triggered for Order ID: %s", instance.id)

    send_email = False

    if created:
        logger.info("✅ This is a new order, sending email...")
        send_email = True
    else:
        if hasattr(instance, 'status') and instance.status and instance.status.lower() == 'hired':
            logger.info("🔄 Order marked as hired, sending email...")
            send_email = True

    if send_email:
        # Inverter details
        if instance.inverter_id:
            inverter_parts = [
                instance.inverter_id.given_start_name or "",
                instance.inverter_id.model or "",
                instance.inverter_id.serial_no or "",
            ]
            inverter_name = " ".join(filter(None, inverter_parts))
        else:
            inverter_name = "N/A"

        # Email content
        subject = 'New Purchase Order Created'
        message = f"""
A new Purchase Order has been created or updated to Hired.

PO Number     : {instance.po_number}
Contract No   : {instance.contract_no}
Client        : {instance.issued_to.client_name if instance.issued_to else 'N/A'}
Start Date    : {instance.start_date}
Inverter      : {inverter_name}
End Date      : {instance.end_date}
Location      : {instance.location_id or 'N/A'}
Remarks       : {instance.remarks or 'None'}
"""

        from_email = settings.DEFAULT_FROM_EMAIL

        # Recipients
        recipient_list = [
            'steevo@offgridenergy.ie',
            'Jp@generatorhire.ie',
            'anna@offgridenergy.ie',
            'David@horizonplant.com',
            'swathy.horizonoffgrid@gmail.com',
            'john@generatorhire.ie',
            # 'renjurenjithrajendran@gmail.com'
        ]

        if instance.issued_to and instance.issued_to.client_email:
            recipient_list.append(instance.issued_to.client_email)

        # Send email
        try:
            sent_count = send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False
            )
            if sent_count:
                logger.info(f"✅ Email sent to {', '.join(recipient_list)} for PO {instance.po_number}")
            else:
                logger.warning(f"❌ Email not sent for PO {instance.po_number}")
        except Exception as e:
            logger.error(f"❌ Error sending email for PO {instance.po_number}: {str(e)}")
