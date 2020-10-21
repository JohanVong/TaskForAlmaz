from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import Task, TaskStatusUpdate
from .serializers import TaskSerializer, UserSerializer, TaskStatusUpdateSerializer

import threading

# Здесь ведется работа над механизмом, который периодически запрашивать все задания и если найдет
# просроченные, то изменит их статус и отправит сообщения о просрочке оператору и наблюдателям

# ВНИМАНИЕ ВНИМАНИЕ !!! 
# механизм еще не готов ;(
# посему на данный момент, срабатывает только один раз при запуске сервера
# а еще с этим куском кода нельзя провести самую первую 'makemigrations' 
# когда база данных только создана, поэтому он закомментирован

INITIAL_STATUSES = ('planning', 'active', 'inactive', 'testing')
STATUSES = ('planning', 'active', 'inactive', 'testing', 'completed')
UNTOUCHABLE_STATUSES = ('completed', 'failed')

def check_tasks(*args, **kwargs):
    threading.Timer(10.0, check_tasks).start()
    tasks = Task.objects.all()
    for tsk in tasks:
        if timezone.now() > tsk.planned_end and tsk.task_status not in UNTOUCHABLE_STATUSES:
            tsk.task_status = 'failed'
            tsk.save()
            # отправляем уведомление оператору
            opr = tsk.operator_id
            print("Send notification to: " + str(opr.username) + ", Time is up for task '{0}'!".format(tsk.title))
            # отправляем уведомления наблюдателям
            rcps = tsk.observers_id.all()
            for rcp in rcps:
                print("Send notification to: " + str(rcp.username) + ", Time is up for task '{0}'!".format(tsk.title))
    print("Checking statuses...")

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
        user = request.user
        if 'title' in request.data:
            title = request.data['title']
        else:
            response = {'message': "Field 'title' is mandatory in a request data"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if 'desc' in request.data:
            desc = request.data['desc']
        else:
            desc = None

        operator_id = User.objects.get(id=user.id)

        if 'task_status' in request.data:  
            task_status = request.data['task_status']
            if task_status not in INITIAL_STATUSES:
                response = {'message': "Wrong status given"}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': "Field 'task_status' is mandatory in a request data"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        started_at = timezone.now()

        # Планируемая дата окончания - обязательное поле для каждой задачи
        # В теле ошибки приведён пример формата времени, который можно использовать
        if 'planned_end' in request.data:
            planned_end = request.data['planned_end']
        else:
            response = {'message': "Field 'planned_end' is mandatory in a request data", 'example': "2020-12-30T00:00:00Z"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        task = Task.objects.create(
            title=title, desc=desc, 
            operator_id=operator_id, task_status=task_status, 
            started_at=started_at,
            planned_end=planned_end,
        )

        # При указании наблюдателей в теле запроса нужно давать их 'username' а не 'id'
        # 'id' будут извллечены с помощью предоставленных 'username' наблюдателей
        if 'observers_id' in request.data:
            obs_list = request.data['observers_id']
            for obs in obs_list:
                observer = User.objects.get(username=obs)
                task.observers_id.add(observer)
        else:
            obs_list = None

        task.save()
        serializer = TaskSerializer(task, many=False)
        response = {'message': 'Task created', 'result': serializer.data}
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['PUT'], authentication_classes = [TokenAuthentication])
    def task_update(self, request, pk=None):
        user = request.user
        task = Task.objects.get(id=pk)
        
        # Выполненные или проваленные задания нельзя редактировать
        if task.task_status == 'completed' or task.task_status == 'failed':
            response = {'message': "Completed or failed tasks are disabled for updates"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if 'title' in request.data:
            response = {'message': "Field 'title' can not be changed once it was created"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if 'desc' in request.data:
            task.desc = request.data['desc']
        
        # Только оператор может изменить статус задачи, за исключением
        # случая, когда задача истекла по времени т.е - провалена
        # Примечание: Можно изменить в будущем
        operator_id = User.objects.get(id=user.id)
        if task.operator_id != operator_id:
            response = {'message': "Only operator of a task can edit it"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if 'task_status' in request.data:
            prev_status = task.task_status  
            task.task_status = request.data['task_status']
            if task.task_status not in STATUSES:
                response = {'message': "Wrong status given"}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if task.task_status == 'Completed':
                task.ended_at = timezone.now()
            if prev_status != task.task_status:
                TaskStatusUpdate.objects.create(
                    prev_status=prev_status, next_status=task.task_status, 
                    task_id=task, editor_id=operator_id, update_time=timezone.now()
                )
                recipients = task.observers_id.all()
                # Ниже мы пишем механизм для отправки наблюдателям уведомления
                # об изменении статуса задания. На данный момент вместо этого
                # просто используется print имён наблюдателей 
                for recipient in recipients:
                    # Начало механизма отпраки
                    print('Send notification to: ' + str(recipient.username)) 
                    # Конец механизма отправки
                
        if 'planned_end' in request.data:
            task.planned_end = request.data['planned_end']
        
        # Если при обновлении задания ввести 'username' наблюдателей, 
        # то этот новый список перепишет уже существующий
        if 'observers_id' in request.data:
            task.observers_id.clear()
            obs_list = request.data['observers_id']
            for obs in obs_list:
                observer = User.objects.get(username=obs)
                task.observers.add(observer)
        
        task.save()
        serializer = TaskSerializer(task, many=False)
        response = {'message': 'Task updated', 'result': serializer.data}
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

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
