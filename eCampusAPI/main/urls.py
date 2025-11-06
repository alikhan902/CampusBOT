from rest_framework import routers
from .views import InstituteAPI, ScheduleView
from django.urls import path, include

router = routers.SimpleRouter()
router.register(r'Institute', InstituteAPI)

urlpatterns = [
    path('', include(router.urls)),
    path('schedule/', ScheduleView.as_view(), name='schedule'),
]