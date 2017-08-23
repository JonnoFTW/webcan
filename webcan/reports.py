from pyramid.view import view_config
from .views import get_device_trips_for_user

@view_config(route_name='report_list', renderer="templates/reports/list_reports.mako")
def report_list(request):
    introspector = request.registry.introspector
    reports = [
        i for i in introspector._categories['routes'].values() if i['pattern'].startswith('/report/') and '{' not in i['pattern']
    ]
    return {'reports': reports}


@view_config(route_name='report_phase', renderer="templates/reports/phase_classify.mako")
def phase_classify(request):
    return {'trips': get_device_trips_for_user(request)}


@view_config(route_name='report_phase_classify', renderer="json")
def phase_classify_render(request):
    return {'readings': []}
