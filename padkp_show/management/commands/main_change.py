from padkp_show.models import main_change

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Perform a main change, transferring DKP and attendance'

    def add_arguments(self, parser):
        parser.add_argument('character_from')
        parser.add_argument('character_to')

    def handle(self, *args, **options):
        print(args)
        main_change(options['character_from'], options['character_to'])
