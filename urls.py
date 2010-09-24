from django.conf.urls.defaults import *
from django.contrib.auth.models import User
from volsched.sched.models import *
#from django.contrib import admin

urlpatterns = patterns(
    '',
# Sitemap
    (r'sitemap/$', 'volsched.sched.views.sitemap'),
# The index page
    (r'^$', 'volsched.sched.views.index'),
    (r'^copyright/$', 'volsched.sched.views.copyright'),
    (r'^contact/(?P<type>\w+)/$', 'volsched.sched.views.contact'),
# Event views
    (r'^event/new/$', 'volsched.sched.views.event_new'),
    (r'^event/(?P<event_id>\d+)/$', 'volsched.sched.views.event_details'),
    (r'^event/(?P<event_id>\d+)/edit/$', 'volsched.sched.views.event_edit'),
    (r'^event/(?P<event_id>\d+)/delete/$', 'volsched.sched.views.event_delete'),
# Job views
    (r'^event/(?P<event_id>\d+)/job/new/$', 'volsched.sched.views.job_new'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/$', 'volsched.sched.views.job_details'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/edit/$', 'volsched.sched.views.job_edit'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/delete/$', 'volsched.sched.views.job_delete'),
# Shift views
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/shift/new/$', 'volsched.sched.views.shift_new'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/shift/(?P<shift_id>\d+)/edit/$', 'volsched.sched.views.shift_edit'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/shift/(?P<shift_id>\d+)/delete/$', 'volsched.sched.views.shift_delete'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/shift/(?P<shift_id>\d+)/signup/$', 'volsched.sched.views.shift_signup'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/shift/(?P<shift_id>\d+)/unsignup/$', 'volsched.sched.views.shift_unsignup'),
# Signup views
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/signups/$', 'volsched.sched.views.signups_view'),
    (r'^event/(?P<event_id>\d+)/signups/$', 'volsched.sched.views.signups_view'),
    (r'^event/(?P<event_id>\d+)/volunteers/$', 'volsched.sched.views.volunteers_view'),
    (r'^event/(?P<event_id>\d+)/job/(?P<job_id>\d+)/signups/remind/$', 'volsched.sched.views.send_reminder'),
    (r'^event/(?P<event_id>\d+)/signups/remind/$', 'volsched.sched.views.send_reminder'),
# User management views
    (r'^user/register/$', 'volsched.sched.views.user_register'),
    (r'^user/login/$', 
     'django.contrib.auth.views.login',
     {'template_name': 'user_login.html'}),
    (r'^accounts/login/$', 
     'django.contrib.auth.views.login',
     {'template_name': 'user_login.html' }),
    (r'^user/logout/$',
     'django.contrib.auth.views.logout',
     {'template_name': 'user_logout.html'}),
    (r'^user/confirm/(?P<username>.+?)/(?P<activation_key>\w+)/$', 'volsched.sched.views.user_confirm'),
    (r'^confirm/(?P<username>.+)/(?P<activation_key>\w+)/$', 'volsched.sched.views.user_confirm'),
    (r'^user/password_change/$',
     'django.contrib.auth.views.password_change',
     {'template_name': 'user_password.html'}),
    (r'^user/password_change/done/$',
     'django.contrib.auth.views.password_change_done',
     {'template_name': 'user_password.html'}),
# Convenient admin
#    (r'^admin/', include('django.contrib.admin.urls')),
)
