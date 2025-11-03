from datetime import datetime, timedelta
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
        date_str = request.GET.get('date')
        group_name = request.GET.get('group')
        teacher_name = request.GET.get('teacher')
        room_name = request.GET.get('room')

        if not date_str:
            return Response({"error": "Параметр 'date' обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            monday = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Неверный формат даты (используй YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)

        week_dates = [monday + timedelta(days=i) for i in range(7)]

        filters = Q(date__in=week_dates)
        if group_name:
            filters &= Q(group__Name__iexact=group_name)
        if teacher_name:
            filters &= Q(teacher__Name__iexact=teacher_name)
        if room_name:
            filters &= Q(room__Name__iexact=room_name)

        lessons = Lesson.objects.filter(filters).order_by('date', 'time_begin')
        serializer = LessonSerializer(lessons, many=True)

        return Response(serializer.data)