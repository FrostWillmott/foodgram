import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Load ingredients from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file containing the ingredients')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        with open(json_file, 'r', encoding='utf-8') as file:
            ingredients_list = json.load(file)

        for ingredient_data in ingredients_list:
            ingredient, created = Ingredient.objects.get_or_create(
                name=ingredient_data['name'],
                defaults={'measurement_unit': ingredient_data['measurement_unit']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Successfully added {ingredient.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"{ingredient.name} already exists"))