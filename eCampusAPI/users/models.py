from django.db import models

class BotUser(models.Model):
    user_id = models.BigIntegerField(unique=True)
    ecampus_id = models.CharField(max_length=255, default="", blank=True)
    cookies = models.TextField()
