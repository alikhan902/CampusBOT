from rest_framework import routers
from .views import BotUserAPI
from django.urls import path, include

router = routers.SimpleRouter()
router.register(r'BotUser', BotUserAPI)

urlpatterns = [
    path('', include(router.urls)),
]