import datetime, random, sha
from django.shortcuts import render_to_response
from volsched.sched.models import *
from volsched.sched.forms import *
from django.core.mail import send_mail
from django import newforms as forms
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.views import login
from django.contrib.auth.decorators import login_required

def sitemap(request):
    return HttpResponseRedirect("http://static.volsched.com/sitemap.xml")

def index(request):
    if request.user.is_authenticated():
        public_events = Event.objects.filter(public__exact = True, start_date__gte = datetime.date.today()).exclude(owner__exact = request.user).order_by('start_date')
        my_events_upcoming = Event.objects.filter(owner__exact = request.user, end_date__gte = datetime.date.today()).order_by('start_date')
        my_events_past = Event.objects.filter(owner__exact = request.user, end_date__lt = datetime.date.today()).order_by('start_date')
        signups = request.user.signup_set.all()
        my_shifts = []
        for s in signups:
            if s.shift.start_time.date() >= datetime.date.today():
                my_shifts.append(s.shift)
        return render_to_response('index.html', { 'my_events_upcoming': my_events_upcoming, 'my_events_past': my_events_past, 'public_events': public_events, 'my_shifts': my_shifts }, context_instance=RequestContext(request))

    public_events = Event.objects.filter(public__exact = True, start_date__gte = datetime.date.today()).order_by('start_date')
    return render_to_response('index.html', { 'public_events': public_events }, context_instance=RequestContext(request))

def copyright(request):
    return render_to_response('copyright.html', context_instance=RequestContext(request))

@login_required
def contact(request, type):
    if type == 'bug':
        title = 'Bug Report or Feature Request'
        to = 'bugs@volsched.com'
    elif type == 'spam':
        title = 'Spam Report'
        to = 'abuse@volsched.com'
    else:
        return render_to_response('contact.html', { 'badtype': True }, context_instance=RequestContext(request))        

    if request.method == 'POST':
        f = MessageForm(request.POST)

        if f.is_valid():
            f.sendmessage(to, request.user.email)
            return render_to_response('contact.html', { 'sent': True, 'title': title }, context_instance=RequestContext(request))

    else:
        f = MessageForm()

    return render_to_response('contact.html', {'form': f, 'title': title}, context_instance = RequestContext(request))

@login_required
def event_new(request):
    if request.method == 'POST':
        f = EventForm(request.POST)
        
        if f.is_valid():
            new_event = f.process()
            new_event.owner = request.user
            new_event.save()
            
            return HttpResponseRedirect("/event/%d" % new_event.id)
    else:
        f = EventForm()

    return render_to_response('sched/event_form.html', {'form': f, 'action': 'new'}, context_instance = RequestContext(request))

@login_required
def event_delete(request, event_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/event_delete.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/event_delete.html', {'wronguser': True}, context_instance = RequestContext(request))

    if request.method == 'POST':
        if 'notify' in request.POST and request.POST['notify']:
            jobs = e.job_set.all()
            signups = []
            for j in jobs:
                for s in list(j.shift_set.all()):
                    for su in list(s.signup_set.all()):
                        signups.append(su)

            people = [su.person for su in signups]
            people = list(set(people))

            # REMEMBER TO CHANGE
            baseurl = 'www.volsched.com'

            email_subject = 'Event %s' % e.name
            email_body = '%s,\n\n'
            email_body += 'The administrator of the event %s has chosen to delete this event, for which you were signed up.\n\n'
            email_body += 'Thank you for using Volsched.\n'

            for person in people:
                send_mail(email_subject,
                          email_body % (person.first_name, e.name),
                          'VolSched Notifier <notifications@volsched.com>',
                          [person.email])

        e.delete()
        return render_to_response('sched/event_delete.html', {'deleted': True, 'event': e}, context_instance = RequestContext(request))
    else:
        return render_to_response('sched/event_delete.html', {'confirm': True, 'event': e}, context_instance = RequestContext(request))

@login_required
def event_edit(request, event_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/event_form.html', {'notfound': True, 'action': 'edit'}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/event_form.html', {'wronguser': True, 'action': 'edit'}, context_instance = RequestContext(request))
    
    if request.method == 'POST':
        f = EventForm(request.POST)

        if f.is_valid():
            newe = f.process()
            
            bad_shifts = []
            jobs = Job.objects.all().filter(event__exact = e)
            for j in jobs:
                shifts = Shift.objects.all().filter(job__exact = j)
                for s in shifts:
                    if s.start_time.date() < newe.start_date or s.end_time.date() > newe.end_date:
                        bad_shifts.append(s)
            if len(bad_shifts) > 0:
                if 'whattodo' in request.POST and request.POST['whattodo'] == 'delete':
                    [s.delete() for s in bad_shifts]
                else:
                    return render_to_response('sched/event_form.html', {'form': f, 'action': 'edit', 'badshifts': True}, context_instance = RequestContext(request))

            e.name = newe.name
            e.start_date = newe.start_date
            e.end_date = newe.end_date
            e.description = newe.description
            e.public = newe.public
            e.save()
            return HttpResponseRedirect("/event/%d" % e.id)
    else:
        f = EventForm({'event_name': e.name, 'start_date': e.start_date, 'end_date': e.end_date, 'description': e.description, 'public': e.public})

    return render_to_response('sched/event_form.html', {'form': f, 'action': 'edit'}, context_instance = RequestContext(request))

def event_details(request, event_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/event_details.html', {'notfound': True}, context_instance = RequestContext(request))

    try:
        j = Job.objects.all().filter(event__exact = e).order_by('name')
    except Job.DoesNotExist:
        j = {}

    if request.user.is_authenticated():
        signups = request.user.signup_set.all()
        myshifts = []
        for s in signups:
            if s.shift.job.event == e:
                myshifts.append(s.shift)
    else:
        myshifts = None
    
    return render_to_response('sched/event_details.html', {'event': e, 'jobs': j, 'myshifts': myshifts}, context_instance = RequestContext(request))

@login_required
def job_new(request, event_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/job_form.html', {'action': 'new', 'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/job_form.html', {'action': 'new', 'wronguser': True}, context_instance = RequestContext(request))

    if request.method == 'POST':
        f = JobForm(request.POST)
        
        if f.is_valid():
            new_job = f.process()
            new_job.event = e
            new_job.save()
            
            return HttpResponseRedirect("/event/%d/job/%d" % (e.id,new_job.id))
    else:
        f = JobForm()
        
    return render_to_response('sched/job_form.html', {'action': 'new', 'form': f, 'event': e}, context_instance = RequestContext(request))

@login_required
def job_delete(request, event_id, job_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/job_delete.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/job_delete.html', {'wronguser': True}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/job_delete.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/job_delete.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    if request.method == 'POST':
        if 'notify' in request.POST and request.POST['notify']:
            shifts = list(j.shift_set.all())
            signups = []
            for s in shifts:
                for su in list(s.signup_set.all()):
                    signups.append(su)
            people = [su.person for su in signups]
            people = list(set(people))

            # REMEMBER TO CHANGE
            baseurl = 'www.volsched.com'

            email_subject = 'Your job at %s' % e.name
            email_body = '%s,\n\n'
            email_body += 'The administrator of the event %s has deleted the job %s, which you were signed up to do.\n\n'
            email_body += 'You can view the event details at:\n\n'
            email_body += 'http://%s/event/%d/\n\n'
            email_body += 'Thank you for using Volsched.\n'

            for person in people:
                send_mail(email_subject,
                          email_body % (person.first_name, e.name, j.name, baseurl, e.id),
                          'VolSched Notifier <notifications@volsched.com>',
                          [person.email])

        j.delete()
        return HttpResponseRedirect("/event/%d" % e.id)
    else:
        return render_to_response('sched/job_delete.html', {'confirm': True, 'job': j, 'event': e}, context_instance = RequestContext(request))

@login_required
def job_edit(request, event_id, job_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/job_form.html', {'eventnotfound': True, 'action': 'edit'}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/job_form.html', {'wronguser': True, 'action': 'edit'}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/job_form.html', {'jobnotfound': True, 'action': 'edit'}, context_instance = RequestContext(request))
    
    if request.method == 'POST':
        f = JobForm(request.POST)

        if f.is_valid():
            newj = f.process()
            
            j.name = newj.name
            j.description = newj.description
            j.save()
            return HttpResponseRedirect("/event/%d/job/%d" % (e.id, j.id))
    else:
        f = JobForm({'job_name': j.name, 'description': j.description})

    return render_to_response('sched/job_form.html', {'form': f, 'event': e, 'action': 'edit'}, context_instance = RequestContext(request))

def job_details(request, event_id, job_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/job_details.html', {'eventnotfound': True}, context_instance = RequestContext(request))
    
    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/job_details.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/job_details.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    try:
        allshifts = list(Shift.objects.all().filter(job__exact = j).order_by('start_time'))
    except Shift.DoesNotExist:
        allshifts = []

    fullshifts = []
    myshifts = []

    for shift in allshifts:
        shift.number_required -= shift.signup_set.count()
        if shift.number_required == 0:
            fullshifts.append(shift)
            
        if request.user.is_authenticated():
            signups = shift.signup_set.filter(person__exact = request.user)
            if signups.count() > 0:
                myshifts.append(shift)

    for shift in myshifts:
        if shift in fullshifts:
            fullshifts.remove(shift)
        if shift in allshifts:
            allshifts.remove(shift)
    for shift in fullshifts:
        if shift in allshifts:
            allshifts.remove(shift)

    return render_to_response('sched/job_details.html', {'event': e, 'job': j, 'shifts': allshifts, 'fullshifts': fullshifts, 'myshifts': myshifts}, context_instance = RequestContext(request))

@login_required
def shift_new(request, event_id, job_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/shift_form.html', {'eventnotfound': True, 'action': 'new'}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/shift_form.html', {'wronguser': True, 'action': 'new'}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/shift_form.html', {'jobnotfound': True, 'action': 'new'}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/shift_form.html', {'jobnotfound': True, 'action': 'new'}, context_instance = RequestContext(request))

    if request.method == 'POST':
        f = ShiftForm(request.POST)
        
        if f.is_valid():
            new_shift = f.process()
            new_shift.job = j
            if new_shift.start_time.date() < e.start_date or new_shift.end_time.date() > e.end_date:
                return render_to_response('sched/shift_form.html', {'form': f, 'badtimes': True, 'event': e, 'job': j, 'action': 'new'}, context_instance = RequestContext(request))
            new_shift.save()
            
            return HttpResponseRedirect("/event/%d/job/%d" % (j.event.id, j.id))
    else:
        f = ShiftForm()
        
    return render_to_response('sched/shift_form.html', {'form': f, 'event': e, 'job': j, 'action': 'new'}, context_instance = RequestContext(request))

@login_required
def shift_delete(request, event_id, job_id, shift_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/shift_delete.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/shift_delete.html', {'wronguser': True}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/shift_delete.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/shift_delete.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    try:
        s = Shift.objects.get(id = shift_id)
    except Shift.DoesNotExist:
        return render_to_response('sched/shift_delete.html', {'shiftnotfound': True}, context_instance = RequestContext(request))

    if s.job != j:
        return render_to_response('sched/shift_delete.html', {'shiftnotfound': True}, context_instance = RequestContext(request))

    if request.method == 'POST':
        if 'notify' in request.POST and request.POST['notify']:
            signups = list(Signup.objects.all().filter(shift__exact = s))
            people = [su.person for su in signups]

            # REMEMBER TO CHANGE
            baseurl = 'www.volsched.com'

            email_subject = 'Your %s shift at %s' % (j.name, e.name)
            email_body = '%s,\n\n'
            email_body += 'The administrator of the event %s has deleted your %s shift from %s to %s.\n\n'
            email_body += 'You can view the event details at:\n\n'
            email_body += 'http://%s/event/%d/\n\n'
            email_body += 'Thank you for using Volsched.\n'

            for person in people:
                send_mail(email_subject,
                          email_body % (person.first_name, e.name, j.name, s.start_time.strftime('%a %F %d, %Y %H:%M'), s.end_time.strftime('%a %F %d, %Y %H:%M'), baseurl, e.id),
                          'VolSched Notifier <notifications@volsched.com>',
                          [person.email])

        s.delete()

        return render_to_response('sched/shift_delete.html', {'deleted': True, 'event': e, 'job': j}, context_instance = RequestContext(request))
    else:
        return render_to_response('sched/shift_delete.html', {'confirm': True, 'shift': s, 'job': j, 'event': e}, context_instance = RequestContext(request))

@login_required
def shift_edit(request, event_id, job_id, shift_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/shift_form.html', {'eventnotfound': True, 'action': 'edit'}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/shift_form.html', {'wronguser': True, 'action': 'edit'}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/shift_form.html', {'jobnotfound': True, 'action': 'edit'}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/shift_form.html', {'jobnotfound': True, 'action': 'edit'}, context_instance = RequestContext(request))

    try:
        s = Shift.objects.get(id = shift_id)
    except Shift.DoesNotExist:
        return render_to_response('sched/shift_form.html', {'shiftnotfound': True, 'action': edit}, context_instance = RequestContext(request))

    if s.job != j:
        return render_to_response('sched/shift_form.html', {'shiftnotfound': True, 'action': edit}, context_instance = RequestContext(request))
    
    if request.method == 'POST':
        f = ShiftForm(request.POST)

        if f.is_valid():
            news = f.process()

            nsignups = s.signup_set.count()
            if nsignups > news.number_required:
                return render_to_response('sched/shift_form.html', {'form': f, 'badrequired': True, 'event': e, 'job': j, 'action': 'edit'}, context_instance = RequestContext(request))

            if 'notify' in request.POST and request.POST['notify'] and (s.start_time != news.start_time or s.end_time != news.end_time):
                signups = list(Signup.objects.all().filter(shift__exact = s))
                people = [su.person for su in signups]
                
                # REMEMBER TO CHANGE
                baseurl = 'www.volsched.com'
                
                email_subject = 'Your %s shift at %s' % (j.name, e.name)
                email_body = '%s,\n\n'
                email_body += 'The administrator of the event %s has changed the time of your %s shift:\n\n'
                email_body += 'Old times: %s to %s.\n'
                email_body += 'New times: %s to %s.\n\n'
                email_body += 'You can view the event details at:\n\n'
                email_body += 'http://%s/event/%d/\n\n'
                email_body += 'Thank you for using Volsched.\n'
                
                for person in people:
                    send_mail(email_subject,
                              email_body % (person.first_name, e.name, j.name, s.start_time.strftime('%a %F %d, %Y %H:%M'), s.end_time.strftime('%a %F %d, %Y %H:%M'), news.start_time.strftime('%a %F %d, %Y %H:%M'), news.end_time.strftime('%a %F %d, %Y %H:%M'), baseurl, e.id),
                              'VolSched Notifier <notifications@volsched.com>',
                              [person.email])

            s.start_time = news.start_time
            s.end_time = news.end_time
            s.number_required = news.number_required
            s.save()
            return HttpResponseRedirect("/event/%d/job/%d" % (e.id, j.id))

    else:
        f = ShiftForm({'start_time': s.start_time, 'end_time': s.end_time, 'number_required': s.number_required})

    return render_to_response('sched/shift_form.html', {'form': f, 'event': e, 'job': j, 'action': 'edit'}, context_instance = RequestContext(request))

@login_required
def shift_signup(request, event_id, job_id, shift_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/shift_signup.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    try:
        s = Shift.objects.get(id = shift_id)
    except Shift.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'shiftnotfound': True}, context_instance = RequestContext(request))

    if s.job != j:
        return render_to_response('sched/shift_signup.html', {'shiftnotfound': True}, context_instance = RequestContext(request))

    usershifts = request.user.signup_set.all();
    for u in usershifts:
        if s.overlaps(u.shift):
            return render_to_response('sched/shift_signup.html', {'overlap': True, 'badshift': u.shift, 'event': e, 'job': j, 'shift': s}, context_instance = RequestContext(request))
        
    sign = Signup()
    sign.shift = s
    sign.person = request.user
    sign.save()

    return HttpResponseRedirect("/event/%d/job/%d" % (j.event.id, j.id))

@login_required
def shift_unsignup(request, event_id, job_id, shift_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    try:
        j = Job.objects.get(id = job_id)
    except Job.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    if j.event != e:
        return render_to_response('sched/shift_signup.html', {'jobnotfound': True}, context_instance = RequestContext(request))

    try:
        s = Shift.objects.get(id = shift_id)
    except Shift.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'shiftnotfound': True}, context_instance = RequestContext(request))

    if s.job != j:
        return render_to_response('sched/shift_signup.html', {'shiftnotfound': True}, context_instance = RequestContext(request))

    try:
        sign = Signup.objects.all().filter(person__exact = request.user, shift__exact = s)
    except Signup.DoesNotExist:
        return render_to_response('sched/shift_signup.html', {'notsignedup': True}, context_instance = RequestContext(request))

    sign.delete()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def signups_view(request, event_id, job_id = None):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/signups_view.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/signups_view.html', {'wronguser': True}, context_instance = RequestContext(request))

    if job_id:
        try:
            jobs = [Job.objects.get(id = job_id)]
        except Job.DoesNotExist:
            return render_to_response('sched/signups_view.html', {'jobnotfound': True}, context_instance = RequestContext(request))
        if jobs[0].event != e:
            return render_to_response('sched/signups_view.html', {'jobnotfound': True}, context_instance = RequestContext(request))
    else:
        jobs = e.job_set.all()

    signups = []
    for j in jobs:
        for shift in j.shift_set.all():
            for signup in shift.signup_set.all():
                signups.append(signup)

    signups.sort(key = lambda u: u.shift.start_time)
    if job_id:
        return render_to_response('sched/signups_view.html', {'signups': signups, 'event': e, 'job': jobs[0]}, context_instance = RequestContext(request))
    else:
        return render_to_response('sched/signups_view.html', {'signups': signups, 'event': e}, context_instance = RequestContext(request))

@login_required
def volunteers_view(request, event_id):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/volunteers_view.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/volunteers_view.html', {'wronguser': True}, context_instance = RequestContext(request))

    jobs = e.job_set.all()

    people = []
    for j in jobs:
        for shift in j.shift_set.all():
            for signup in shift.signup_set.all():
                if not signup.person in people:
                    people.append(signup.person)

    people.sort(key = lambda p: p.last_name)
    return render_to_response('sched/volunteers_view.html', {'people': people, 'event': e}, context_instance = RequestContext(request))

@login_required
def send_reminder(request, event_id, job_id = None):
    try:
        e = Event.objects.get(id = event_id)
    except Event.DoesNotExist:
        return render_to_response('sched/send_reminder.html', {'eventnotfound': True}, context_instance = RequestContext(request))

    if e.owner != request.user:
        return render_to_response('sched/send_reminder.html', {'wronguser': True}, context_instance = RequestContext(request))

    if job_id:
        try:
            jobs = [Job.objects.get(id = job_id)]
        except Job.DoesNotExist:
            return render_to_response('sched/send_reminder.html', {'jobnotfound': True}, context_instance = RequestContext(request))
        if jobs[0].event != e:
            return render_to_response('sched/send_reminder.html', {'jobnotfound': True}, context_instance = RequestContext(request))
    else:
        jobs = e.job_set.all()

    people = []
    for j in jobs:
        for s in j.shift_set.all():
            for su in s.signup_set.all():
                if not su.person in people:
                    people.append(su.person)

    shifts = []
    for j in jobs:
        shifts.extend(j.shift_set.all())

    # REMEMBER TO CHANGE
    baseurl = 'www.volsched.com'

    for person in people:
        signups = person.signup_set.filter(shift__in = shifts)

        myshifts = [su.shift for su in signups]
        myshifts.sort(key = lambda s: s.start_time)

        if job_id:
            email_subject = 'Your %s Shifts at %s' % (jobs[0].name, e.name)
        else:
            email_subject = 'Your Shifts at %s' % e.name

        email_body = '%s,\n\nThis email is to remind you about the shifts you''ve signed up for at %s:\n\n' % (person.first_name, e.name)
        for s in myshifts:
            email_body += '%s to %s - %s\n' % (s.start_time.strftime('%a %F %d, %Y %H:%M'), s.end_time.strftime('%a %F %d, %Y %H:%M'), s.job.name)

        email_body += '\nYou can view the event details at:\n\n'
        email_body += 'http://%s/event/%d/\n\n' % (baseurl,e.id)
        email_body += 'Thank you for using VolSched!\n'

        send_mail(email_subject,
                  email_body,
                  'VolSched Notifier <notifications@volsched.com>',
                  [person.email])

    if job_id:
        return render_to_response('sched/send_reminder.html', {'event': e, 'job': jobs[0]}, context_instance = RequestContext(request))        
    else:
        return render_to_response('sched/send_reminder.html', {'event': e}, context_instance = RequestContext(request))

def user_register(request):
    if request.method == 'POST':
        m = RegistrationForm(request.POST)

        if m.is_valid():
            new_user = m.save()

            activation_key = sha.new(new_user.username).hexdigest()

            # REMEMBER TO CHANGE
            baseurl = 'www.volsched.com'
            
            # Send an email with the confirmation link
            email_subject = 'Your VolSched Registration'
            email_body = "%s,\n\nThank you for signing up for a VolSched account.  " % new_user.first_name
            email_body += "To activate your account, click this link:\n\n"
            email_body += "http://%s/user/confirm/%s/%s\n\n" % (baseurl, new_user.username.replace(" ","%20"), activation_key)
            email_body += "Enjoy VolSched!\n"
            
            send_mail(email_subject,
                      email_body,
                      'VolSched Account Administrator <accounts@volsched.com>',
                      [new_user.email])
            
            return render_to_response('user_register.html', {'created': True}, context_instance = RequestContext(request))
    else:
        m = RegistrationForm()

    return render_to_response('user_register.html', {'form': m}, context_instance = RequestContext(request))

def user_confirm(request, username, activation_key):
    if request.user.is_authenticated():
        return render_to_response('user_confirm.html', {'has_account': True}, context_instance = RequestContext(request))
    
    try:
        u = User.objects.get(username = username)
    except User.DoesNotExist:
        return render_to_response('user_confirm.html', {'no_such_user': True}, context_instance = RequestContext(request))
    
    correct_key = sha.new(username).hexdigest()
    
    if activation_key != correct_key:
        return render_to_response('user_confirm.html', {'invalid_key': True}, context_instance = RequestContext(request))

    u.is_active = True
    u.save()

    return render_to_response('user_confirm.html', {'success': True}, context_instance = RequestContext(request))
