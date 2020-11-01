from django.utils import timezone
from django.forms.models import model_to_dict
from django.core import serializers

from api.models import Task, TaskStatusUpdate, TaskReminder

from .celery import app

import threading
import time
import json
import requests


UNTOUCHABLE_STATUSES = ('completed', 'failed')


@app.task
def notify(emails, is_failed, pk=None):
    tsk = Task.objects.get(id=pk)
    tsk_rmndr = TaskReminder.objects.create(
        task_id=tsk, taskname=tsk.title,
        recipients=emails, is_failed=is_failed
    )
    dict_obj = model_to_dict(tsk_rmndr)
    serialized = json.dumps(dict_obj)
    if len(tsk_rmndr.recipients) != 0:
        r = requests.post('http://localhost:8080/send/mails', data=serialized)
        if r.status_code == 200:
            print('Data was sent properly')
        else:
            print('Data was not sent properly')
    else:
        tsk_rmndr.delete()
        print('No data to send')


@app.task
def check_tasks(*args, **kwargs):
    tasks = Task.objects.all()
    emails = []
    for tsk in tasks:
        if timezone.now() > tsk.planned_end and tsk.task_status not in UNTOUCHABLE_STATUSES:
            prev_status = tsk.task_status 
            tsk.task_status = 'failed'
            tsk.ended_at = timezone.now()
            tsk.save()
            # отправляем уведомления наблюдателям
            rcps = tsk.observers_id.all()
            for rcp in rcps:
                emails.append(rcp.email)
            # отправляем уведомление оператору если его нет в наблюдателях
            opr = tsk.operator_id
            if opr.email not in emails:
                emails.append(opr.email)
            TaskStatusUpdate.objects.create(
                prev_status=prev_status, next_status=tsk.task_status, 
                task_id=tsk, editor_id=tsk.operator_id, update_time=timezone.now()
            )
            notify(pk=tsk.id, emails=emails, is_failed=True)
    print("Checking statuses...")
    