from rest_framework import viewsets
from .models import Institute, Lesson
from .serializers import InstituteSerializer, LessonSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from collections import defaultdict

class InstituteAPI(viewsets.ModelViewSet):
    queryset = Institute.objects.all()
    serializer_class = InstituteSerializer
    
class ScheduleView(APIView):
    def get(self, request):
        group_name = request.GET.get('group')
        teacher_name = request.GET.get('teacher')
        room_name = request.GET.get('room')

        filters = Q()
        if group_name:
            filters &= Q(group__Name__icontains=group_name)
        if teacher_name:
            filters &= Q(teacher__Name__icontains=teacher_name)
        if room_name:
            filters &= Q(room__Name__icontains=room_name)

        lessons = Lesson.objects.filter(filters).order_by('date', 'time_begin')

        serializer = LessonSerializer(lessons, many=True)


        grouped = defaultdict(list)
        for lesson in serializer.data:
            grouped[str(lesson['date'])].append(lesson)

        result = [
            {"date": date, "lessons": lessons}
            for date, lessons in sorted(grouped.items(), key=lambda x: x[0])
        ]

        return Response(result, status=status.HTTP_200_OK)