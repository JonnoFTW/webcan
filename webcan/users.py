from .views import USER_LEVELS, LOGIN_TYPES, AJAXHttpBadRequest
import pyramid.httpexceptions as exc
from pyramid.view import view_config
import secrets
import bcrypt
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
    new_fan = request.POST.get('new-fan')
    level = request.POST.get('new-level')
    login_type = request.POST.get('new-login')
    if new_fan is None or re.findall(r"^[\w_]+$", new_fan) == []:
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
    if login_type == 'external':
        password = secrets.token_hex(32)
        new_user_obj['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user_obj['reset_password'] = secrets.token_urlsafe(16)
    request.db.webcan_users.insert_one(new_user_obj)
    return new_user_obj


@view_config(route_name='user_manage', renderer='bson')
def user_manage(request):
    user_id = request.matchdict['user_id']
    if request.user['level'] != 'admin' and user_id != request.user['username']:
        raise exc.HTTPForbidden("You can only view your own user page")
    else:
        return request.db.webcan_users.find_one({'username': user_id})


@view_config(route_name='reset_user_password', renderer='bson')
def set_password_reset(request):
    url = secrets.token_urlsafe(16)
    username = request.matchdict['user_id']
    request.db.webcan_users.update_one({'username': username},
                                       {'$set': {'reset_password': url}})
    return {
        'url': '{}/reset_password?reset_key={}'.format(request.application_url, url)
    }


@view_config(route_name='external_reset', renderer='templates/simple/reset_pass.mako')
def external_password_reset(request):
    key = request.GET.get('reset_key', None)
    if key is None:
        msg = "No reset key provided"

    else:
        user = request.db.webcan_users.find_one({'reset_password': key})
        if user is None:
            msg = 'No such reset key'
        else:
            # reset the user's key and show them their password
            del user['reset_password']
            password = secrets.token_hex(32).encode('utf-8')

            user['password'] = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
            msg = "Your new password is: {}<br>Please record this and <a href='/login'>login</a>".format(
                password.decode('utf-8'),
            )
            request.db.webcan_users.replace_one({'_id': user['_id']}, user)
    return {'msg': msg}
