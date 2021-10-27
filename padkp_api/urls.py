from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'characters', views.CharacterViewSet)
router.register(r'awards', views.DkpSpecialAwardViewSet)
router.register(r'upload_dump', views.UploadRaidDump)
router.register(r'upload_casual_dump', views.UploadCasualRaidDump)
router.register(r'charge_dkp', views.ChargeDKP)
router.register(r'tiebreak', views.Tiebreak)
router.register(r'second_class', views.SecondClassCitizens)
router.register(r'resolve_auction', views.ResolveAuction, basename='api')
router.register(r'correct_auction', views.CorrectAuction, basename='api')
router.register(r'cancel_auction', views.CancelAuction, basename='api')
router.register(r'resolve_flags', views.ResolveFlags, basename='api')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
