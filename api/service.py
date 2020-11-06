from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import status

from .models import Task, TaskStatusUpdate
from .serializers import TaskSerializer, UserSerializer, TaskStatusUpdateSerializer, TaskReminderSerializer
from TaskManagerByAlmaz.tasks import notify


INITIAL_STATUSES = ('planning', 'active', 'inactive', 'testing')
STATUSES = ('planning', 'active', 'inactive', 'testing', 'completed')


def create_task(self, request, pk=None):
    try:
        user = request.user

        if 'title' in request.data:
            title = request.data['title']
        else:
            response = 'Title missing error'
            return response

        if 'desc' in request.data:
            desc = request.data['desc']
        else:
            desc = None

        operator_id = User.objects.get(id=user.id)

        if 'task_status' in request.data:  
            task_status = request.data['task_status']
            if task_status not in INITIAL_STATUSES:
                response = 'Wrong status given error'
                return response
        else:
            response = 'Task status missing error'
            return response

        started_at = timezone.now()

        # Планируемая дата окончания - обязательное поле для каждой задачи
        # В теле ошибки приведён пример формата времени, который можно использовать
        if 'planned_end' in request.data:
            planned_end = request.data['planned_end']
        else:
            response = 'Planned end missing error, clear example: 2020-12-30T00:00Z'
            return response

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
                try:
                    observer = User.objects.get(username=obs)
                    task.observers_id.add(observer)
                except:
                    None
        else:
            obs_list = None

        task.save()
        serializer = TaskSerializer(task, many=False)
        response = serializer.data
        return response
        
    except:
        response = "Unknown service error"
        return response


def update_task(self, request, task_to_update):
    try:
        user = request.user
        emails = []
        prev_status = task_to_update.task_status 
        
        # Выполненные или проваленные задания нельзя редактировать
        if task_to_update.task_status == 'completed' or task_to_update.task_status == 'failed':
            response = 'Update restriction for completed or failed tasks error'
            return response

        if 'title' in request.data:
            response = 'Task title change restriction error'
            return response

        if 'desc' in request.data:
            task_to_update.desc = request.data['desc']
        
        # Только оператор может изменить статус задачи, за исключением
        # случая, когда задача истекла по времени т.е - провалена
        operator_id = User.objects.get(id=user.id)
        if task_to_update.operator_id != operator_id:
            response = "Access restriction error"
            return response
                
        if 'planned_end' in request.data:
            task_to_update.planned_end = request.data['planned_end']
        
        # Список наблюдателей заполняется путем передачи 'username' наблюдателя
        # если добавить уже существующий 'username', он удалится из списка
        if 'observers_id' in request.data:
            obs_list = request.data['observers_id']
            for obs in obs_list:
                try:
                    observer = User.objects.get(username=obs)
                    if observer in task_to_update.observers_id.all():
                        task_to_update.observers_id.remove(observer)
                    else:
                        task_to_update.observers_id.add(observer)
                except:
                    None

        if 'task_status' in request.data:
            task_to_update.task_status = request.data['task_status']
            if task_to_update.task_status not in STATUSES:
                response = 'Wrong status given error'
                return response
            if task_to_update.task_status == 'completed':
                task_to_update.ended_at = timezone.now() 
        
        task_to_update.last_update = timezone.now()
        
        task_to_update.save()

        # Создаем запись об обновлении и рассылаем уведомления, 
        # если старый статус задачи не равен новому
        if prev_status != task_to_update.task_status:
            TaskStatusUpdate.objects.create(
                prev_status=prev_status, next_status=task_to_update.task_status, 
                task_id=task_to_update, editor_id=operator_id, update_time=timezone.now()
            )
            recipients = task_to_update.observers_id.all()
            for recipient in recipients:
                emails.append(recipient.email)
            notify.delay(pk=task_to_update.id, emails=emails, reason=task_to_update.task_status)
            
        serializer = TaskSerializer(task_to_update, many=False)
        response = serializer.data
        return response

    except: 
        response = "Unknown service error"
        return response
        