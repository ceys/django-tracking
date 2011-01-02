from django.conf.urls.defaults import *
from django.conf import settings
from tracking import views

urlpatterns = patterns('',
    url(r'^refresh/$', views.update_active_users, name='tracking-refresh-active-users'),
    url(r'^refresh/json/$', views.get_active_users, name='tracking-get-active-users'),

    # django-tracking analytics
    url(r'^analytics/views/$', views._page_views, name='tracking-analytics-views'),
    url(r'^analytics/visitors/$', views._page_visitors, name='tracking-analytics-visitors'),
    url(r'^analytics/$', views.analytics_home, name='tracking-analytics-home'),
)

if getattr(settings, 'TRACKING_USE_GEOIP', False):
    urlpatterns += patterns('',
        url(r'^map/$', views.display_map, name='tracking-visitor-map'),
    )
