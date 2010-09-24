import datetime
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django import newforms as forms
from django.newforms import ValidationError
from django.core import validators
from django.contrib.auth import login, authenticate
from volsched.sched.models import *
import volsched.sched.widgets as widgets

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length = 30)
    email = forms.EmailField()
    first_name = forms.CharField(max_length = 30)
    last_name = forms.CharField(max_length = 30)
    password1 = forms.CharField(max_length = 60, widget = forms.PasswordInput, label = 'Password')
    password2 = forms.CharField(max_length = 60, widget = forms.PasswordInput, label = 'Confirm Password')
    
    def clean_username(self):
        n = self.clean_data['username']
        try:
            User.objects.get(username = n)
        except User.DoesNotExist:
            return self.clean_data['username']
        raise ValidationError('The username "%s" is already taken.' % n)

    def clean(self):
        if 'password1' in self.clean_data and 'password2' in self.clean_data:
            if self.clean_data['password1'] != self.clean_data['password2']:
                raise ValidationError('Passwords must match.')

        return self.clean_data
        
    def save(self):
        u = User.objects.create_user(username = self.clean_data['username'],
                                     email = self.clean_data['email'],
                                     password = self.clean_data['password1']);
        u.first_name = self.clean_data['first_name']
        u.last_name = self.clean_data['last_name']
        u.is_active = False
        u.save()
        return u

class EventForm(forms.Form):
    event_name = forms.CharField(max_length = 100)
    start_date = forms.DateField(widget = widgets.DateWidget)
    end_date = forms.DateField(widget = widgets.DateWidget)
    description = forms.CharField(widget = forms.Textarea)
    public = forms.BooleanField(label = 'Make this event public', required = False)
    
    def clean_start_date(self):
        if 'start_date' in self.clean_data:
            if self.clean_data['start_date'] < datetime.date.today():
                raise ValidationError('Event must start later than today.')

        return self.clean_data['start_date']

    def clean(self):
        if 'start_date' in self.clean_data and 'end_date' in self.clean_data:
            if self.clean_data['start_date'] > self.clean_data['end_date']:
                raise ValidationError('Event cannot end before it begins.')
            
        return self.clean_data

    def process(self):
        e = Event()
        e.name = self.clean_data['event_name']
        e.start_date = self.clean_data['start_date']
        e.end_date = self.clean_data['end_date']
        e.description = self.clean_data['description']
        e.public = self.clean_data['public']
        
        return e

class JobForm(forms.Form):
    job_name = forms.CharField(max_length = 100)
    description = forms.CharField(widget = forms.Textarea)
    
    def process(self):
        j = Job()
        j.name = self.clean_data['job_name']
        j.description = self.clean_data['description']
        
        return j

class ShiftForm(forms.Form):
    start_time = forms.DateTimeField(widget = widgets.DateTimeWidget)
    end_time = forms.DateTimeField(widget = widgets.DateTimeWidget)
    number_required = forms.IntegerField()
    
    def clean_number_required(self):
        if 'number_required' in self.clean_data:
            if self.clean_data['number_required'] <= 0:
                raise ValidationError('Number required must be positive.')
        return self.clean_data['number_required']

    def clean(self):
        if 'start_time' in self.clean_data and 'end_time' in self.clean_data:
            if self.clean_data['start_time'] > self.clean_data['end_time']:
                raise ValidationError('Shift cannot end before it begins.')
            
        return self.clean_data

    def process(self):
        s = Shift()
        s.start_time = self.clean_data['start_time']
        s.end_time = self.clean_data['end_time']
        s.number_required = self.clean_data['number_required']
        
        return s

class MessageForm(forms.Form):
    subject = forms.CharField(max_length = 100)
    message = forms.CharField(widget = forms.Textarea)

    def sendmessage(self, toemail, fromemail):
        send_mail(self.clean_data['subject'],
                  self.clean_data['message'],
                  fromemail,
                  [toemail])
