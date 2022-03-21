from django.test import TestCase
from padkp_show.models import Character, RaidDump, CharacterAlt, Purchase
from padkp_show.models import main_change
from django.utils import timezone
import datetime as dt


class MainChangeTests(TestCase):

    def setUp(self):
        self.char1 = Character.objects.create(name='Lancegar', status='MN')
        self.char2 = Character.objects.create(name='Seped', status='ALT')
        CharacterAlt.objects.create(name='Seped', main=self.char1)
        CharacterAlt.objects.create(name='AnotherAlt', main=self.char1)
        time = timezone.now()
        dump = RaidDump(value=10, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([self.char1])

        time = timezone.now()
        dump = RaidDump(value=4, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([self.char2])

        Purchase(
            character=self.char1,
            item_name='Awesome Shiny',
            value=2,
            time=time,
            is_alt=1,
        ).save()

        Purchase(
            character=self.char1,
            item_name='Awesome Shiny2',
            value=3,
            time=time,
            is_alt=0,
        ).save()

        Purchase(
            character=self.char2,
            item_name='Awesome Alt Shiny2',
            value=3,
            time=time,
            is_alt=1,
        ).save()

    def test_main_change_alt_settings_cleared(self):
        main_change('Lancegar', 'Seped')

        self.char1.refresh_from_db()
        self.char2.refresh_from_db()

        alt_listing, = CharacterAlt.objects.filter(name='Lancegar')
        other_alts, = CharacterAlt.objects.filter(name='AnotherAlt')
        removed_alts = CharacterAlt.objects.filter(name='Seped')

        self.assertEqual(self.char1.status, 'ALT')
        self.assertEqual(self.char2.status, 'MN')
        self.assertEqual(alt_listing.main.name, 'Seped')
        self.assertEqual(other_alts.main.name, 'Seped')
        self.assertEqual(removed_alts.count(), 0)

    def test_main_change_alt_assignment_when_none_exists(self):
        alt_listing, = CharacterAlt.objects.filter(name='Seped')
        alt_listing.delete()

        main_change('Lancegar', 'Seped')

        self.char1.refresh_from_db()
        self.char2.refresh_from_db()

        alt_listing, = CharacterAlt.objects.filter(name='Lancegar')
        other_alts, = CharacterAlt.objects.filter(name='AnotherAlt')

        self.assertEqual(self.char1.status, 'ALT')
        self.assertEqual(self.char2.status, 'MN')
        self.assertEqual(alt_listing.main.name, 'Seped')
        self.assertEqual(other_alts.main.name, 'Seped')

    def test_main_change_dkp_maintained(self):
        main_change('Lancegar', 'Seped')

        self.char1.refresh_from_db()
        self.char2.refresh_from_db()

        self.assertEqual(self.char1.current_dkp(), 0)
        self.assertEqual(self.char2.current_dkp(), 7)
        self.assertEqual(self.char2.current_alt_dkp(), 8)
