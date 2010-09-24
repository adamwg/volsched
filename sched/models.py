from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    owner = models.ForeignKey(User)
    name = models.CharField(maxlength = 100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    public = models.BooleanField()
    
class Job(models.Model):
    event = models.ForeignKey(Event)
    name = models.CharField(maxlength = 100)
    description = models.TextField()
    
class Shift(models.Model):
    job = models.ForeignKey(Job)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    number_required = models.IntegerField()

    def overlaps(self, s):
        return (s.start_time <= self.start_time and s.end_time > self.start_time) or \
            (s.start_time < self.end_time and s.end_time >= self.end_time) or \
            (self.start_time <= s.start_time < self.end_time and \
                 self.start_time < s.end_time < self.end_time)

class Signup(models.Model):
    shift = models.ForeignKey(Shift)
    person = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add = True)
