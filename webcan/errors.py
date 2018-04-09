import pymongo
from pyramid.view import forbidden_view_config, notfound_view_config, exception_view_config, view_config
from webob import exc


@forbidden_view_config(renderer='templates/exceptions/403.mako')
def forbidden(request):
    request.response.status = 403
    return {}


@notfound_view_config(renderer='templates/exceptions/404.mako')
def notfound(request):
    request.response.status = 404
    return {}


@exception_view_config(pymongo.errors.NetworkTimeout, renderer='templates/exceptions/503.mako')
def service_unavailable(request):
    return {'msg': 'Server too busy or your query took too long'}


@exception_view_config(pymongo.errors.ConnectionFailure, renderer='templates/exceptions/503.mako')
def connection_failure(request):
    return {'msg': 'Server connection timeout'}


@exception_view_config(pymongo.errors.ServerSelectionTimeoutError, renderer='templates/exceptions/503.mako')
def service_unselectable(request):
    return {'msg': 'Can\'t find database server'}


@view_config(context=exc.HTTPBadRequest)
def bad_request(exception, request):
    if request.is_xhr:
        return exception
    return exception


class AJAXHttpBadRequest(exc.HTTPBadRequest):
    def doJson(self, status, body, title, environ):
        return {'message': self.detail,
                'code': status,
                'title': self.title}

    def __init__(self, detail):
        exc.HTTPBadRequest.__init__(self, detail, json_formatter=self.doJson)

        self.content_type = 'application/json'
