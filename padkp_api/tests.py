from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from padkp_show.models import Character, RaidDump, CharacterAlt, Purchase, Auction, AuctionBid
from django.utils import timezone
from django.urls import resolve
import json
import hashlib
import datetime as dt


class CorrectAuctionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        char1 = Character.objects.create(name='Lancegar', status='MN')
        CharacterAlt.objects.create(name='Seped', main=char1)
        char2 = Character.objects.create(name='Quaff', status='MN')
        char3 = Character.objects.create(name='Quaff2', status='MN')
        char4 = Character.objects.create(name='LowBid', status='MN')
        char5 = Character.objects.create(name='RecruitBid', status='Recruit')
        Character.objects.create(name='Bid', status='MN')
        time = timezone.now()
        dump = RaidDump(value=20, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char2, char3, char4, char5])

        dump = RaidDump(value=0, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char3])

    def test_single_auction_correction_only(self):
        bids = [{'name': 'Lancegar', 'bid': '7', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '2', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        rdata = {'bids': bids, 'item_count': item_count, 'item_name': item_name,
                 'fingerprint': 'testfingerprint', 'time': time}

        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func
        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()

        bids = [{'name': 'Quaff', 'bid': '6', 'tag': ''}]
        rdata = {'bids': bids, 'fingerprint': 'testfingerprint'}
        request = factory.post('/api/correct_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        view = resolve(request.get_full_path()).func
        response = view(request)
        response.render()

        data = eval(response.content)
        char, = Character.objects.filter(name='Quaff')
        lance, = Character.objects.filter(name='Lancegar')
        purchase, = Purchase.objects.filter(character=char, value=6)
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(data, 'Auction corrected')
        self.assertEqual(char.current_dkp(), 14)
        self.assertEqual(lance.current_dkp(), 20)
        self.assertEqual(len(auction.auctionbid_set.all()), 3)
        self.assertEqual(auction, purchase.auction)

    def test_single_auction_correction_for_alt(self):
        bids = [{'name': 'Lancegar', 'bid': '7', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '2', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        rdata = {'bids': bids, 'item_count': item_count, 'item_name': item_name,
                 'fingerprint': 'testfingerprint', 'time': time}

        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func
        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()

        bids = [{'name': 'Quaff\'s alt', 'bid': '6'}]
        rdata = {'bids': bids, 'fingerprint': 'testfingerprint'}
        request = factory.post('/api/correct_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        view = resolve(request.get_full_path()).func
        response = view(request)
        response.render()

        data = eval(response.content)
        char, = Character.objects.filter(name='Quaff')
        lance, = Character.objects.filter(name='Lancegar')
        purchase, = Purchase.objects.filter(character=char, value=6)
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(data, 'Auction corrected')
        self.assertEqual(char.current_dkp(), 20)
        self.assertEqual(char.current_alt_dkp(), 14)
        self.assertEqual(lance.current_dkp(), 20)
        self.assertEqual(len(auction.auctionbid_set.all()), 3)
        self.assertEqual(auction, purchase.auction)

    def test_single_auction_multiple_correction(self):
        bids = [{'name': 'Seped', 'bid': '2', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '7', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 2
        time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        rdata = {'bids': bids, 'item_count': item_count, 'item_name': item_name,
                 'fingerprint': 'testfingerprint', 'time': time}
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func
        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()

        bids = [{'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'Seped', 'bid': '7', 'tag': ''}]
        rdata = {'bids': bids, 'fingerprint': 'testfingerprint'}
        request = factory.post('/api/correct_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        view = resolve(request.get_full_path()).func
        response = view(request)
        response.render()

        data = eval(response.content)
        char, = Character.objects.filter(name='LowBid')
        lance, = Character.objects.filter(name='Lancegar')
        quaff, = Character.objects.filter(name='Quaff')
        purchase, = Purchase.objects.filter(
            character=lance, value=7, is_alt=True)
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(data, 'Auction corrected')
        self.assertEqual(char.current_dkp(), 20)
        self.assertEqual(quaff.current_dkp(), 14)
        self.assertEqual(lance.current_alt_dkp(), 13)
        self.assertEqual(len(auction.auctionbid_set.all()), 3)
        self.assertEqual(auction, purchase.auction)
        self.assertTrue(auction.corrected)


class CancelAuctionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        char1 = Character.objects.create(name='Lancegar', status='MN')
        CharacterAlt.objects.create(name='Seped', main=char1)
        char2 = Character.objects.create(name='Quaff', status='MN')
        char3 = Character.objects.create(name='Quaff2', status='MN')
        char4 = Character.objects.create(name='LowBid', status='MN')
        char5 = Character.objects.create(name='RecruitBid', status='Recruit')
        Character.objects.create(name='Bid', status='MN')
        time = timezone.now()
        dump = RaidDump(value=20, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char2, char3, char4, char5])

        dump = RaidDump(value=0, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char3])

    def test_cancel_failing_on_old_auctions(self):
        bids = [{'name': 'Lancegar', 'bid': '7', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '2', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        time = (dt.datetime.utcnow() - dt.timedelta(hours=3)
                ).strftime('%Y-%m-%dT%H:%M:%SZ')
        rdata = {'bids': bids, 'item_count': item_count, 'item_name': item_name,
                 'fingerprint': 'testfingerprint', 'time': time}
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func
        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()

        rdata = {'fingerprint': 'testfingerprint'}
        request = factory.post('/api/cancel_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        view = resolve(request.get_full_path()).func
        response = view(request)
        response.render()

        data = eval(response.content)
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(data, 'Auction is more than two hours old')
        self.assertIsNotNone(auction)

    def test_auction_multiple_canceled(self):
        bids = [{'name': 'Seped', 'bid': '2', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '7', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 2
        time = (dt.datetime.utcnow() - dt.timedelta(hours=1)
                ).strftime('%Y-%m-%dT%H:%M:%SZ')
        rdata = {'bids': bids, 'item_count': item_count, 'item_name': item_name,
                 'fingerprint': 'testfingerprint', 'time': time}
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func
        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()

        rdata = {'fingerprint': 'testfingerprint'}
        request = factory.post('/api/cancel_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        view = resolve(request.get_full_path()).func
        response = view(request)
        response.render()

        data = eval(response.content)
        auctions = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        abids = AuctionBid.objects.all()
        purchases = Purchase.objects.filter(auction__isnull=False)
        char, = Character.objects.filter(name='LowBid')

        self.assertEqual(data, 'Auction canceled')
        self.assertEqual(len(auctions), 0)
        self.assertEqual(len(abids), 0)
        self.assertEqual(len(purchases), 0)
        self.assertEqual(char.current_dkp(), 20)


class ResolveAuctionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        char1 = Character.objects.create(name='Lancegar', status='MN')
        CharacterAlt.objects.create(name='Seped', main=char1)
        char2 = Character.objects.create(name='Quaff', status='MN')
        char3 = Character.objects.create(name='Quaff2', status='MN')
        char4 = Character.objects.create(name='LowBid', status='MN')
        char5 = Character.objects.create(name='RecruitBid', status='Recruit')
        Character.objects.create(name='Bid', status='MN')
        time = timezone.now()
        dump = RaidDump(value=20, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char2, char3, char4, char5])

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

    def build_auction_json(self, bids, item_count, item_name, time=dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')):
        fingerprint = hashlib.sha256(
            '{}-{}-{}'.format(json.dumps(bids), item_count, item_name).encode('utf-8')).hexdigest()
        return {'bids': bids, 'item_count': item_count, 'item_name': item_name, 'fingerprint': fingerprint, 'time': time}

    def test_no_tie_single_auction_main_only(self):
        bids = [{'name': 'Lancegar', 'bid': '7', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '2', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        purchase, = Purchase.objects.filter(character=char, value=7)
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Test Item awarded to - Lancegar for 7')
        self.assertEqual(char.current_dkp(), 13)
        self.assertEqual(len(auction.auctionbid_set.all()), 3)
        self.assertEqual(auction, purchase.auction)

    def test_warnings_on_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '21', 'tag': ''},
                {'name': 'RecruitBid', 'bid': '6', 'tag': ''},
                {'name': 'NotRealBidder', 'bid': '6', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        self.assertEqual(
            data['message'], 'Test Item awarded to - Lancegar for 21')
        self.assertEqual(len(data['warnings']), 3)
        self.assertEqual(
            data['warnings'][0], 'Lancegar bid 21 dkp but only has 20 on the site')
        self.assertEqual(
            data['warnings'][1], 'RecruitBid bid with tag "" but is registered as "Recruit"')
        self.assertEqual(
            data['warnings'][2], 'Received bid for unknown character: NotRealBidder')

    def test_fnf_cutoff_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '11', 'tag': ''},
                {'name': 'RecruitBid', 'bid': '15', 'tag': 'Recruit'}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        self.assertEqual(
            data['message'], 'Test Item awarded to - Lancegar for 11')
        self.assertEqual(len(data['warnings']), 0)

    def test_alt_cutoff_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '11', 'tag': 'ALT'},
                {'name': 'RecruitBid', 'bid': '15', 'tag': 'Recruit'}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        self.assertEqual(
            data['message'], 'Test Item awarded to - RecruitBid for 15')
        self.assertEqual(len(data['warnings']), 0)

    def test_alt_cutoff_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '11', 'tag': 'ALT'},
                {'name': 'RecruitBid', 'bid': '15', 'tag': 'Recruit'}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        self.assertEqual(
            data['message'], 'Test Item awarded to - RecruitBid for 15')
        self.assertEqual(len(data['warnings']), 0)

    def test_alt_win_message_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '11', 'tag': 'ALT'},
                {'name': 'RecruitBid', 'bid': '5', 'tag': 'Recruit'}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        self.assertEqual(
            data['message'], "Test Item awarded to - Lancegar's alt for 11")
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(char.current_alt_dkp(), 7)

    def test_alt_win_message_when_alt_bids(self):
        bids = [{'name': 'Seped', 'bid': '11', 'tag': ''},
                {'name': 'RecruitBid', 'bid': '5', 'tag': 'Recruit'}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        bid, = AuctionBid.objects.filter(character=char)
        self.assertEqual(
            data['message'], "Test Item awarded to - Lancegar's alt for 11")
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(char.current_alt_dkp(), 7)
        self.assertEqual(bid.tag, 'ALT')

    def test_alt_win_message_when_alt_bids_as_main(self):
        bids = [{'name': 'Seped', 'bid': '11', 'tag': 'Main'},
                {'name': 'RecruitBid', 'bid': '5', 'tag': 'Recruit'}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        bid, = AuctionBid.objects.filter(character=char)
        self.assertEqual(
            data['message'], "Test Item awarded to - Lancegar for 11")
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(char.current_alt_dkp(), 18)
        self.assertEqual(char.current_dkp(), 9)
        self.assertEqual(bid.tag, 'Main')

    def test_two_auctions_in_a_row_only(self):
        bids = [{'name': 'Lancegar', 'bid': '7', 'tag': ''},
                {'name': 'Quaff', 'bid': '6', 'tag': ''},
                {'name': 'LowBid', 'bid': '2', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        view = resolve(request.get_full_path()).func
        response = view(request)
        response.render()

        item_name = 'Another Item'
        rdata = self.build_auction_json(bids, item_count, item_name)

        request = factory.post('/api/resolve_auction/', rdata, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        char, = Character.objects.filter(name='Lancegar')
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Another Item awarded to - Lancegar for 7')
        self.assertEqual(char.current_dkp(), 6)

    def test_tie_message_format(self):
        bids = [{'name': 'Lancegar', 'bid': '15', 'tag': ''},
                {'name': 'Quaff', 'bid': '15', 'tag': ''},
                {'name': 'RecruitBid', 'bid': '15', 'tag': ''},
                {'name': 'LowBid', 'bid': '14', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        lance, = Character.objects.filter(name='Lancegar')
        quaff, = Character.objects.filter(name='Quaff')
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Test Item awarded to - Lancegar for 15 - Quaff, RecruitBid Lost the tie')
        self.assertEqual(lance.current_dkp(), 5)
        self.assertEqual(len(auction.auctionbid_set.all()), 4)

    def test_multi_item_complicated_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '15', 'tag': ''},
                {'name': 'Quaff', 'bid': '15', 'tag': ''},
                {'name': 'LowBid', 'bid': '14', 'tag': ''},
                {'name': 'RecruitBid', 'bid': '20', 'tag': 'ALT'}]
        item_name = 'Test Item'
        item_count = 3
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        lance, = Character.objects.filter(name='Lancegar')
        quaff, = Character.objects.filter(name='Quaff')
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Test Item awarded to - Lancegar for 15, Quaff for 15, LowBid for 14')
        self.assertEqual(lance.current_dkp(), 5)
        self.assertEqual(quaff.current_dkp(), 5)
        self.assertEqual(len(auction.auctionbid_set.all()), 4)

    def test_multi_item_with_rot(self):
        bids = [{'name': 'Lancegar', 'bid': '15', 'tag': ''},
                {'name': 'Quaff', 'bid': '15', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 3
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        lance, = Character.objects.filter(name='Lancegar')
        quaff, = Character.objects.filter(name='Quaff')
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Test Item awarded to - Lancegar for 15, Quaff for 15, Rot')
        self.assertEqual(lance.current_dkp(), 5)
        self.assertEqual(quaff.current_dkp(), 5)
        self.assertEqual(len(auction.auctionbid_set.all()), 2)

    def test_zero_bid_auction(self):
        bids = [{'name': 'Lancegar', 'bid': '0', 'tag': ''}]
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        lance, = Character.objects.filter(name='Lancegar')
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Test Item awarded to - Rot')
        self.assertEqual(lance.current_dkp(), 20)
        self.assertEqual(len(auction.auctionbid_set.all()), 0)

    def test_no_bid_auction(self):
        bids = []
        item_name = 'Test Item'
        item_count = 1
        rdata = self.build_auction_json(bids, item_count, item_name)
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_auction/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        lance, = Character.objects.filter(name='Lancegar')
        quaff, = Character.objects.filter(name='Quaff')
        auction, = Auction.objects.filter(fingerprint=rdata['fingerprint'])
        self.assertEqual(
            data['message'], 'Test Item awarded to - Rot')
        self.assertEqual(lance.current_dkp(), 20)
        self.assertEqual(len(auction.auctionbid_set.all()), 0)


class TiebreakTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        char1 = Character.objects.create(name='Lancegar', status='MN')
        CharacterAlt.objects.create(name='Seped', main=char1)
        char2 = Character.objects.create(name='Quaff', status='MN')
        char3 = Character.objects.create(name='Quaff2', status='MN')
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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

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
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertEqual(data, 'DKP charge successful')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.char1.current_dkp(), 20)
        self.assertEqual(self.char1.current_alt_dkp(), 15)

class ResolveFlagsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='robert', email='robert@…', password='top_secret')
        char1 = Character.objects.create(name='Lancegar', status='MN')
        CharacterAlt.objects.create(name='Seped', main=char1)
        char2 = Character.objects.create(name='Quaff', status='MN')
        char3 = Character.objects.create(name='Quaff2', status='MN')
        char4 = Character.objects.create(name='LowBid', status='MN')
        char5 = Character.objects.create(name='RecruitBid', status='Recruit')
        Character.objects.create(name='Bid', status='MN')
        time = timezone.now()
        dump = RaidDump(value=20, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char2, char3, char4, char5])

        dump = RaidDump(value=0, attendance_value=1, time=time)
        dump.save()
        dump.characters_present.set([char1, char3, char5])


    def test_flags(self):
        players = ['Lancegar', 'Lancegar', 'RecruitBid', 'NotRealBidder', 'Quaff', 'Quaff2']
        item_name = 'Test Flag'
        item_count = 3
        rdata = {'players': players, 'item_name': item_name, 'item_count': item_count}
        factory = APIRequestFactory()
        request = factory.post('/api/resolve_flags/', rdata, format='json')
        view = resolve(request.get_full_path()).func

        force_authenticate(request, user=self.user)
        response = view(request)
        response.render()
        data = eval(response.content)
        self.assertTrue('Lancegar' in data['message'])
        self.assertTrue('Quaff2' in data['message'])
        self.assertTrue('RecruitBid' in data['message'])
        self.assertEqual(len(data['message'].split(':')[1].split()), 3)
        self.assertEqual(
            data['warnings'][0], 'NotRealBidder not found in system.')


# %%
