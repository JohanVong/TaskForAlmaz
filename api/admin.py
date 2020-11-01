from django.contrib import admin

from .models import Task, TaskStatusUpdate, TaskReminder

admin.site.register(Task)
admin.site.register(TaskStatusUpdate)
admin.site.register(TaskReminder)
