from django.contrib import admin

from .models import Task, TaskStatusUpdate

admin.site.register(Task)
admin.site.register(TaskStatusUpdate)
