import pandas as pds
from matplotlib import pyplot as plt
import datetime as dt
from collections import defaultdict
from padkp_show.models import RaidDump, Character

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Write some stats on 30 day attendance'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        result = []
        days_ago_30 = dt.datetime.now() - dt.timedelta(days=30)
        for raid_dump in RaidDump.objects.filter(time__gte=days_ago_30):
            class_counts = defaultdict(lambda: 0)
            for char in raid_dump.characters_present.all():
                class_counts[char.character_class] += 1
            result.append(class_counts)
        df = pds.DataFrame(result)
        print(df.describe())
        errors = df.std()
        means = df.mean()
        means.plot.bar(yerr=errors)
        plt.title('30-day class distributions for {}'.format(dt.date.today()))
        plt.show()
