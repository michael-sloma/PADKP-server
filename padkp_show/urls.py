from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # ex: /polls/5/
    path('<slug:character>', views.character_dkp, name='dkp'),
    path('awards/<slug:character>', views.character_awards, name='awards'),
    path('purchases/<slug:character>', views.character_purchases, name='purchases'),

]