from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime

from django.contrib.auth.models import User
from .models import Character, Purchase, RaidDump, DkpSpecialAward, main_change, CharacterAlt
from .models import CasualCharacter, CasualDkpSpecialAward, CasualPurchase, CasualRaidDump
from rest_framework.authtoken.models import Token

from pytz import timezone


class PaDkpShowAdminSite(admin.AdminSite):
    site_header = 'PADKP admin'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        urls += [
            path('main_change/<slug:slug>', self.admin_view(self.my_view))
        ]
        return urls

    def my_view(self, request, slug):
        return HttpResponse("Hello {}!".format(slug))


admin_site = PaDkpShowAdminSite(name='padkp_show_admin')

admin_site.register(User)

admin_site.register(Purchase)
admin_site.register(RaidDump)
admin_site.register(DkpSpecialAward)
admin_site.register(Token)

admin_site.register(CasualPurchase)
admin_site.register(CasualRaidDump)
admin_site.register(CasualCharacter)
admin_site.register(CharacterAlt)
admin_site.register(CasualDkpSpecialAward)


class MainChangeForm(forms.Form):
    main_change_to = forms.CharField(max_length=100)


class CharacterForm(forms.ModelForm):
    class Meta:
        exclude = []
        model = Character

    main_change = forms.ModelChoiceField(
        Character.objects.filter(status='ALT'), required=False)
    add_to_dumps_starting = forms.SplitDateTimeField(
        widget=AdminSplitDateTime, required=False)
    add_to_dumps_ending = forms.SplitDateTimeField(
        widget=AdminSplitDateTime, required=False)

    def clean(self):
        super(CharacterForm, self).clean()
        # This method will set the `cleaned_data` attribute

        start = self.cleaned_data.get('add_to_dumps_starting')
        end = self.cleaned_data.get('add_to_dumps_ending')
        if (start and not end) or (end and not start):
            raise forms.ValidationError(
                'Must provide a both a start and end time to add character to dumps')


class CharacterAdmin(admin.ModelAdmin):
    form = CharacterForm
    list_per_page = 1000

    def main_change(self, request, queryset):
        selected = queryset.values_list('pk', flat=True)
        return HttpResponseRedirect('/admin/main_change/%s' % (
            ','.join(str(pk) for pk in selected),
        ))

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if form.cleaned_data['main_change'] is not None:
            main_change(obj.name, form.cleaned_data['main_change'].name)
        add_start = form.cleaned_data['add_to_dumps_starting']
        add_end = form.cleaned_data['add_to_dumps_ending']
        if add_start and add_end:
            dumps = RaidDump.objects.filter(
                time__gte=add_start, time__lte=add_end)
            for dump in dumps:
                dump.characters_present.add(obj)
        print("DATA", form.cleaned_data)


admin_site.register(Character, CharacterAdmin)
