from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # ex: /polls/5/
    path('attendance/', views.attendance_table, name='dkp'),
    path('awards/', views.awards, name='awards'),
    path('items/', views.items, name='items'),
    path('rules/', views.rules, name='rules'),
    path('<slug:character>/', views.character_dkp, name='dkp'),
]
