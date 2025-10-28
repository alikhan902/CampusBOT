from rest_framework import serializers
from .models import Institute
from .models import Lesson, Teacher, Room, AcademicGroup

class InstituteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institute
        fields = '__all__'
        
class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'Name']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'Name']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicGroup
        fields = ['id', 'Name']

class LessonSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer()
    room = RoomSerializer()
    group = GroupSerializer()

    class Meta:
        model = Lesson
        fields = [
            'lesson_id', 'date', 'weekday', 'discipline', 'lesson_type',
            'time_begin', 'time_end', 'teacher', 'room', 'group', 'subgroup'
        ]
