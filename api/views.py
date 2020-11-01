from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, IsAdminUser
from rest_framework.response import Response

from .service import create_task, update_task
from .models import Task, TaskStatusUpdate, TaskReminder
from .serializers import TaskSerializer, UserSerializer, TaskStatusUpdateSerializer, TaskReminderSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticatedOrReadOnly,]

    def update(self, request, *args, **kwargs):
        response = {'message': 'Prohibited to upgrade by this way'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    def create(self, request, *args, **kwargs):
        response = {'message': 'Prohibited to create by this way'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], authentication_classes = [TokenAuthentication])
    def task_create(self, request, pk=None):
        created_task = create_task(self, request, pk=None)
        
        if 'error' in created_task:
            response = {'message': 'An error occurred', 'error': created_task, 'result': None}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': 'Task created', 'error': None, 'result': created_task}
            return Response(response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['PUT'], authentication_classes = [TokenAuthentication])
    def task_update(self, request, pk=None):
        task_to_update = Task.objects.get(id=pk)
        updated_task = update_task(self, request, task_to_update)

        if 'error' in updated_task:
            response = {'message': 'An error occurred', 'error': updated_task, 'result': None}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': 'Task updated', 'error': None, 'result': updated_task}
            return Response(response, status=status.HTTP_200_OK)
        

class TaskUpdatesViewSet(viewsets.ModelViewSet):
    queryset = TaskStatusUpdate.objects.all()
    serializer_class = TaskStatusUpdateSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticatedOrReadOnly,]

    def update(self, request, *args, **kwargs):
        response = {'message': 'Prohibited to upgrade by this way'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    def create(self, request, *args, **kwargs):
        response = {'message': 'Prohibited to create by this way'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TaskRemindersViewSet(viewsets.ModelViewSet):
    queryset = TaskReminder.objects.all()
    serializer_class = TaskReminderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticatedOrReadOnly,]

    def update(self, request, *args, **kwargs):
        response = {'message': 'Prohibited to upgrade by this way'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    def create(self, request, *args, **kwargs):
        response = {'message': 'Prohibited to create by this way'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
