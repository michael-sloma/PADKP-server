from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # ex: /polls/5/
    path('attendance/', views.attendance_table, name='dkp'),
    path('<slug:character>/', views.character_dkp, name='dkp'),
]
