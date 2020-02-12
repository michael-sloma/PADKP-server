from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django import forms

from .models import Character, Purchase, RaidDump, DkpSpecialAward, main_change
from rest_framework.authtoken.models import Token


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

admin_site.register(Purchase)
admin_site.register(RaidDump)
admin_site.register(DkpSpecialAward)
admin_site.register(Token)


class MainChangeForm(forms.Form):
    main_change_to = forms.CharField(max_length=100)

class CharacterForm(forms.ModelForm):
    class Metal:
        model = Character
    main_change = forms.ModelChoiceField(Character.objects.filter(status='ALT'), required=False)


class CharacterAdmin(admin.ModelAdmin):
    form = CharacterForm

    def main_change(self, request, queryset):
        selected = queryset.values_list('pk', flat=True)
        return HttpResponseRedirect('/admin/main_change/%s' % (
            ','.join(str(pk) for pk in selected),
        ))

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if form.cleaned_data['main_change'] is not None:
            main_change(obj.name, form.cleaned_data['main_change'].name)

admin_site.register(Character, CharacterAdmin)

