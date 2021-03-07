from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from padkp_show.models import Character, RaidDump, CharacterAlt, Purchase
from .views import Tiebreak, ChargeDKP
from django.utils import timezone
import datetime as dt


class TiebreakTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        char1 = Character.objects.create(name='Lancegar', status='Main')
        CharacterAlt.objects.create(name='Seped', main=char1)
        char2 = Character.objects.create(name='Quaff', status='Main')
        char3 = Character.objects.create(name='Quaff2', status='Main')
        time = timezone.now()
        dump = RaidDump(value=10, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char2, char3])

        dump = RaidDump(value=0, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char3])

        Purchase(
            character=char1,
            item_name='Awesome Shiny',
            value=2,
            time=time,
            is_alt=1,
        ).save()

    def test_tiebreak_with_mains_only(self):
        factory = APIRequestFactory()
        request = factory.post(
            '/api/tiebreak/', {'characters': ['Lancegar', 'Quaff']}, format='json')
        view = Tiebreak.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data[0][0], 'Lancegar')
        self.assertEqual(data[1][0], 'Quaff')

    def test_tiebreak_attendance_fallback(self):
        factory = APIRequestFactory()
        request = factory.post(
            '/api/tiebreak/', {'characters': ['Quaff2', 'Quaff']}, format='json')
        view = Tiebreak.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data[0][0], 'Quaff2')
        self.assertEqual(data[1][0], 'Quaff')
        self.assertEqual(
            data[0][1], 'Quaff2 has 10 DKP and 100.00 30-day attendance')

    def test_tiebreak_with_alt_bid(self):
        factory = APIRequestFactory()
        request = factory.post(
            '/api/tiebreak/', {'characters': ["Lancegar's alt", 'Quaff']}, format='json')
        view = Tiebreak.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data[0][0], 'Quaff')
        self.assertEqual(data[1][0], 'Lancegar\'s alt')
        self.assertEqual(
            data[1][1], 'Lancegar\'s alt has 8 DKP and 100.00 30-day attendance')

    def test_tiebreak_with_bid_from_alt(self):
        factory = APIRequestFactory()
        request = factory.post(
            '/api/tiebreak/', {'characters': ['Seped\'s alt', 'Quaff']}, format='json')
        view = Tiebreak.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data[0][0], 'Quaff')
        self.assertEqual(data[1][0], 'Seped\'s alt')
        self.assertEqual(
            data[1][1], 'Seped\'s alt has 8 DKP and 100.00 30-day attendance')

    def test_tiebreak_with_bid_from_alt_no_tag(self):
        factory = APIRequestFactory()
        request = factory.post(
            '/api/tiebreak/', {'characters': ['Seped', 'Quaff']}, format='json')
        view = Tiebreak.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data[0][0], 'Quaff')
        self.assertEqual(data[1][0], 'Seped')
        self.assertEqual(
            data[1][1], 'Seped has 8 DKP and 100.00 30-day attendance')


class ChargeDKPTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        self.char1 = Character.objects.create(name='Lancegar', status='Main')
        CharacterAlt.objects.create(name='Seped', main=self.char1)
        time = timezone.now()
        dump = RaidDump(value=20, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([self.char1])

    def test_charge_dkp_for_main(self):
        factory = APIRequestFactory()
        raw_request = {
            "character": 'Lancegar',
            "item_name": 'Shiny Item',
            "value": 5,
            "time": dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "notes": '',
            "is_alt": False,
        }
        request = factory.post(
            '/api/charge_dkp/', raw_request, format='json')
        view = ChargeDKP.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data, 'DKP charge successful')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.char1.current_dkp(), 15)
        self.assertEqual(self.char1.current_alt_dkp(), 20)

    def test_charge_dkp_for_main_alt(self):
        factory = APIRequestFactory()
        raw_request = {
            "character": 'Lancegar',
            "item_name": 'Shiny Item',
            "value": 5,
            "time": dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "notes": '',
            "is_alt": True,
        }
        request = factory.post(
            '/api/charge_dkp/', raw_request, format='json')
        view = ChargeDKP.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data, 'DKP charge successful')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.char1.current_dkp(), 20)
        self.assertEqual(self.char1.current_alt_dkp(), 15)

    def test_charge_dkp_for_alt(self):
        factory = APIRequestFactory()
        raw_request = {
            "character": 'Seped',
            "item_name": 'Shiny Item',
            "value": 5,
            "time": dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "notes": '',
            "is_alt": False,
        }
        request = factory.post(
            '/api/charge_dkp/', raw_request, format='json')
        view = ChargeDKP.as_view({'post': 'create'})

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data, 'DKP charge successful')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.char1.current_dkp(), 20)
        self.assertEqual(self.char1.current_alt_dkp(), 15)
