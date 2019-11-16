from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
#router.register(r'awards', views.DkpAwardViewSet)
#router.register(r'purchases', views.PurchaseViewSet)
router.register(r'characters', views.CharacterViewSet)
router.register(r'upload_dump', views.UploadRaidDump)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]