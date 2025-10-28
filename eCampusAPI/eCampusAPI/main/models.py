from django.db import models

class Institute(models.Model):
    id = models.IntegerField(primary_key=True)
    ShortName = models.CharField(max_length=10)
    Name = models.CharField(max_length=100)
    BranchId = models.IntegerField(default=1)
    
class Specialty(models.Model):
    Name = models.CharField(max_length=100)
    InstituteID = models.ForeignKey(Institute, on_delete=models.CASCADE)
    
class AcademicGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    Name = models.CharField(max_length=50)
    EduLevel = models.CharField(max_length=50)
    SpecialtyId = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    
class Teacher(models.Model):
    id = models.IntegerField(primary_key=True)
    Name = models.CharField(max_length=100, default='неизвестно')

class Room(models.Model):
    id = models.IntegerField(primary_key=True)
    Name = models.CharField(max_length=50)

class Lesson(models.Model):
    lesson_id = models.IntegerField()
    group = models.ForeignKey(AcademicGroup, on_delete=models.CASCADE)
    date = models.DateField(null=True,blank=True)
    weekday = models.CharField(max_length=20)
    discipline = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=100)
    time_begin = models.TimeField(null=True, blank=True)
    time_end = models.TimeField(null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    subgroup = models.CharField(max_length=20, blank=True, null=True)