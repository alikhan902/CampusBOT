from rest_framework.response import Response
from rest_framework import viewsets
from .models import BotUser
from .serializers import BotUserSerializer
from rest_framework import status

class BotUserAPI(viewsets.ModelViewSet):
    queryset = BotUser.objects.all()
    serializer_class = BotUserSerializer
    
    def create(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = BotUser.objects.get(user_id=user_id)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BotUser.DoesNotExist:
            return super().create(request, *args, **kwargs)