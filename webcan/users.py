from .views import USER_LEVELS, LOGIN_TYPES, AJAXHttpBadRequest
import pyramid.httpexceptions as exc
from pyramid.view import view_config
import secrets
import re


@view_config(route_name='user_list', renderer='templates/users.mako')
def user_list(request):
    return {
        'users': list(request.db.webcan_users.find({}, {'_id': 0, 'password': 0, 'secret': 0})),
        'user_levels': USER_LEVELS,
        'login_types': LOGIN_TYPES
    }


@view_config(route_name='user_add', renderer='bson')
def user_add(request):
    new_fan = request.POST['new-fan']
    level = request.POST['new-level']
    login_type = request.POST['new-login']
    if new_fan and re.findall(r"^[\w_]+$", new_fan) is not None:
        return AJAXHttpBadRequest("Username must only contain underscores, letters and numbers")
    if level not in ('admin', 'viewers'):
        return AJAXHttpBadRequest("User level must be admin or viewers")
    if login_type not in ('ldap', 'external'):
        return AJAXHttpBadRequest("Login type must be ldap or external", )
    if not new_fan or request.db.webcan_users.find_one({'username': new_fan}) is not None:
        return AJAXHttpBadRequest('Empty or existing usernames cannot be used again')
    new_user_obj = {
        'username': new_fan,
        'login': login_type,
        'devices': [],
        'secret': secrets.token_hex(32),
        'level': level
    }

    request.db.webcan_users.insert_one(new_user_obj)
    return new_user_obj


@view_config(route_name='user_manage', renderer='bson')
def user_manage(request):
    user_id = request.matchdict['user_id']
    if request.user['level'] != 'admin' and user_id != request.user['username']:
        raise exc.HTTPForbidden("You can only view your own user page")
    else:
        return request.db.webcan_users.find_one({'username': user_id})
