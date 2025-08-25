import requests
from django.core.management.base import BaseCommand
from order.models import Inverter
from django.conf import settings

VRM_API_URL = "https://vrmapi.victronenergy.com/v2/installations"
VRM_API_KEY = getattr(settings, "VRM_API_KEY", None)  # keep token in settings.py or env

class Command(BaseCommand):
    help = "Sync Inverter installation IDs from VRM portal"

    def handle(self, *args, **kwargs):
        if not VRM_API_KEY:
            self.stdout.write(self.style.ERROR("⚠️ No VRM_API_KEY found in settings."))
            return

        headers = {"X-Authorization": f"Bearer {VRM_API_KEY}"}
        response = requests.get(VRM_API_URL, headers=headers)

        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"❌ Failed to fetch VRM data: {response.text}"))
            return

        data = response.json().get("records", [])
        updated = 0

        for inst in data:
            serial_no = inst.get("device_serial")
            site_id = inst.get("idSite")

            if not serial_no or not site_id:
                continue

            try:
                inverter = Inverter.objects.get(serial_no=serial_no)
                inverter.link_to_installation = str(site_id)
                inverter.save(update_fields=["link_to_installation"])
                updated += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✔ Updated Inverter {inverter.unit_id} -> Site {site_id}"
                ))
            except Inverter.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"⚠ No inverter found for serial {serial_no}"
                ))

        self.stdout.write(self.style.SUCCESS(f"✅ Sync complete. {updated} inverters updated."))
