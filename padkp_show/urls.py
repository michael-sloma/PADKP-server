from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('monday/', views.casual_index, name='casual_index'),
    path('monday/<slug:character>/', views.casual_character_dkp, name='casual_dkp'),
    # ex: /polls/5/
    path('attendance/', views.attendance_table, name='dkp'),
    path('class_balance/', views.class_balance_table, name='class_balance'),
    path('awards/', views.awards, name='awards'),
    path('items/', views.items, name='items'),
    path('rules/', views.rules, name='rules'),
    path('<slug:character>/', views.character_dkp, name='dkp'),
]
