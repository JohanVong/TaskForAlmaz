from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Task, TaskStatusUpdate, TaskReminder


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True, 'required': True}, 'email': {'write_only': True, 'required': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class TaskSerializer(serializers.ModelSerializer):
    operator_id = serializers.SlugRelatedField(slug_field='id', many=False, read_only=True)
    observers_id = serializers.SlugRelatedField(slug_field='id', many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'desc', 
            'operator_id', 'observers_id', 
            'task_status', 'started_at', 
            'ended_at', 'planned_end'
        ]


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    task_id = serializers.SlugRelatedField(slug_field='id', many=False, read_only=True)
    editor_id = serializers.SlugRelatedField(slug_field='id', many=False, read_only=True)

    class Meta:
        model = TaskStatusUpdate
        fields = [
            'id', 'prev_status', 'next_status', 
            'task_id', 'editor_id', 'update_time'
        ]


class TaskReminderSerializer(serializers.ModelSerializer):
    task_id = serializers.SlugRelatedField(slug_field='id', many=False, read_only=True)

    class Meta:
        model = TaskReminder
        fields = [
            'id', 'task_id', 'taskname', 
            'recipients', 'is_failed'
        ]
