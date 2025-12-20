import json
from django.core.management.base import BaseCommand
from users.models import Country, State

class Command(BaseCommand):
    help = 'Load states from local JSON file'

    def handle(self, *args, **kwargs):
        with open('users/management/commands/data/states.json', encoding='utf-8') as f:
            states_data = json.load(f)

        for state in states_data:
            country_name = state['country_name']
            state_name = state['name']
            try:
                country = Country.objects.get(name__iexact=country_name)
            except Country.DoesNotExist:
                self.stderr.write(f"Country not found: {country_name}")
                continue
            State.objects.update_or_create(
                country=country,
                name=state_name
            )
            self.stdout.write(f"Added state {state_name} to {country_name}")