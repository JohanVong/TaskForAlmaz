from django.contrib.auth.models import User
from django.db import models

STATUSES = (
    ('planning', 'planning'),
    ('active', 'active'),
    ('inactive', 'inactive'),
    ('testing', 'testing'),
    ('completed', 'completed'),
    ('failed', 'failed'),
)

class Task(models.Model):
    title = models.CharField(max_length=256, blank=False, null=False)
    desc = models.TextField(blank=True, null=True)
    operator_id = models.ForeignKey(User, on_delete=models.CASCADE)
    observers_id = models.ManyToManyField(User, related_name='%(class)s_id')
    task_status = models.CharField(max_length=64, null=False, blank=False, choices=STATUSES)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    planned_end = models.DateTimeField(blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return self.title

class TaskStatusUpdate(models.Model):
    prev_status = models.CharField(max_length=64, null=False, blank=False, choices=STATUSES)
    next_status = models.CharField(max_length=64, null=False, blank=False, choices=STATUSES)
    task_id = models.ForeignKey(Task, on_delete=models.CASCADE)
    editor_id = models.ForeignKey(User, on_delete=models.PROTECT)
    update_time = models.DateTimeField(blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return "Update of task '{0}'".format(self.task_id)
