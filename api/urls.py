from django.urls import path
from django.conf.urls import include

from rest_framework import routers

from .views import TaskViewSet, UserViewSet, TaskUpdatesViewSet, TaskRemindersViewSet

router = routers.DefaultRouter()
router.register('tasks', TaskViewSet)
router.register('tasks-updates', TaskUpdatesViewSet)
router.register('task-reminders', TaskRemindersViewSet)
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
