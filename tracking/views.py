from datetime import datetime
import logging
import traceback

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.utils.translation import ugettext_lazy as _
from django.utils.simplejson import JSONEncoder
from django.utils.translation import ungettext_lazy, ugettext_lazy as _
from django.views.decorators.cache import never_cache
import pyofc2

from tracking.models import Visitor
from tracking.utils import u_clean as uc

DEFAULT_TRACKING_TEMPLATE = getattr(settings, 'DEFAULT_TRACKING_TEMPLATE',
                                    'tracking/visitor_map.html')
log = logging.getLogger('tracking.views')

def update_active_users(request):
    """
    Returns a list of all active users
    """
    if request.is_ajax():
        active = Visitor.objects.active()
        user = getattr(request, 'user', None)

        info = {
            'active': active,
            'registered': active.filter(user__isnull=False),
            'guests': active.filter(user__isnull=True),
            'user': user
        }

        # render the list of active users
        t = loader.get_template('tracking/_active_users.html')
        c = Context(info)
        users = {'users': t.render(c)}

        return HttpResponse(content=JSONEncoder().encode(users))

    # if the request was not made via AJAX, raise a 404
    raise Http404

@never_cache
def get_active_users(request):
    """
    Retrieves a list of active users which is returned as plain JSON for
    easier manipulation with JavaScript.
    """
    if request.is_ajax():
        active = Visitor.objects.active().reverse()
        now = datetime.now()

        # we don't put the session key or IP address here for security reasons
        try:
            data = {'users': [{
                    'id': v.id,
                    #'user': uc(v.user),
                    'user_agent': uc(v.user_agent),
                    'referrer': uc(v.referrer),
                    'url': uc(v.url),
                    'page_views': v.page_views,
                    'geoip': v.geoip_data_json,
                    'last_update': (now - v.last_update).seconds,
                    'friendly_time': ', '.join(friendly_time((now - v.last_update).seconds)),
                } for v in active]}
        except:
            log.error('There was a problem putting all of the visitor data together:\n%s\n\n%s' % (traceback.format_exc(), locals()))
            return HttpResponse(content='{}', mimetype='text/javascript')

        response = HttpResponse(content=JSONEncoder().encode(data),
                                mimetype='text/javascript')
        response['Content-Length'] = len(response.content)

        return response

    # if the request was not made via AJAX, raise a 404
    raise Http404

def friendly_time(last_update):
    minutes = last_update / 60
    seconds = last_update % 60

    friendly_time = []
    if minutes > 0:
        friendly_time.append(ungettext(
                '%(minutes)i minute',
                '%(minutes)i minutes',
                minutes
        ) % {'minutes': minutes })
    if seconds > 0:
        friendly_time.append(ungettext(
                '%(seconds)i second',
                '%(seconds)i seconds',
                seconds
        ) % {'seconds': seconds })

    return friendly_time or 0

def display_map(request, template_name=DEFAULT_TRACKING_TEMPLATE,
        extends_template='base.html'):
    """
    Displays a map of recently active users.  Requires a Google Maps API key
    and GeoIP in order to be most effective.
    """

    GOOGLE_MAPS_KEY = getattr(settings, 'GOOGLE_MAPS_KEY', None)

    return render_to_response(template_name,
                              {'GOOGLE_MAPS_KEY': GOOGLE_MAPS_KEY,
                               'template': extends_template},
                              context_instance=RequestContext(request))

###
# ANALYTICS
###
def analytics_home(request):
    """Presents the user with some options for viewing analytics information"""

    """
    graph breaking down daily/weekly/monthly visits.
    visits over time in a day
    average peak times
    top referrers graph (top X number of referrers)
    download tracking
    """

    context = RequestContext(request, {
    })

    return render_to_response('admin/tracking/analytics_home.html', context)

def _page_views(request):
    """Returns information about page views"""

    chart = pyofc2.open_flash_chart()
    chart.title = pyofc2.title(text=_('Page Views'))

    return HttpResponse(content=chart.render(), mimetype='text/json')

def _page_visitors(request):
    """Returns information about visitors"""

    chart = pyofc2.open_flash_chart()
    chart.title = pyofc2.title(text=_('Visitors'))

    return HttpResponse(content=chart.render(), mimetype='text/json')
