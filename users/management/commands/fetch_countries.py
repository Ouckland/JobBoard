import requests
from django.core.management.base import BaseCommand
from users.models import Country

class Command(BaseCommand):
    help = 'Fetch countries from REST Countries API and store in DB'

    def handle(self, *args, **options):
        url = 'https://restcountries.com/v3.1/all?fields=name,cca2,idd'  # Fetch phone code too

        response = requests.get(url)
        print(response.status_code)
        if response.status_code != 200:
            self.stderr.write("Failed to fetch countries")
            print(response.text)
            return

        countries = response.json()

        for country in countries:
            name = country.get('name', {}).get('common')
            cca2 = country.get('cca2')  # 2-letter country code

            # Get phone code (idd)
            idd = country.get('idd', {})
            root = idd.get('root', '')
            suffixes = idd.get('suffixes', [''])
            phone_code = root + (suffixes[0] if suffixes and suffixes[0] else '')

            if name and cca2:
                obj, created = Country.objects.update_or_create(
                    code=cca2,
                    defaults={'name': name, 'phone_code': phone_code}
                )
                if created:
                    self.stdout.write(f"Added country: {name} ({phone_code})")
                else:
                    self.stdout.write(f"Updated country: {name} ({phone_code})")