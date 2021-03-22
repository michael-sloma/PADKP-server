from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('casual/', views.casual_index, name='casual_index'),
    path('casual/<slug:character>/', views.casual_character_dkp, name='casual_dkp'),
    # ex: /polls/5/
    path('attendance/', views.attendance_table, name='dkp'),
    path('class_balance/', views.class_balance_table, name='class_balance'),
    path('awards/', views.awards, name='awards'),
    path('items/', views.items, name='items'),
    path('all_items/', views.all_items, name='items'),
    path('rules/', views.rules, name='rules'),
    path('discord/', views.discord, name='discord'),
    path('<slug:character>/', views.character_dkp, name='dkp'),
]
