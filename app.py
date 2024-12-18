#!/usr/bin/env python3

import logging
import os
import ssl
from configparser import ConfigParser
from os import environ, path
from pathlib import Path

import bottle
from bottle import SimpleTemplate
from bottle import get, post, static_file, request, route, template
from ldap3 import Connection, Server, Tls, ALL
from ldap3 import SIMPLE, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPConstraintViolationResult, \
    LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError, \
    LDAPSocketOpenError, LDAPExceptionError

from password_validator import PasswordException, PasswordValidator

BASE_DIR = path.dirname(__file__)
LOG = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
VERSION = '3.0.0'


@get('/')
def get_index():
    return index_tpl()


@post('/')
def post_index():
    form = request.forms.getunicode

    def error(msg):
        return index_tpl(username=form('username'), alerts=[('error', msg)])

    if form('new-password') != form('confirm-password'):
        return error("Passwords are not the same.")

    try:
        LOG.info(f"start password validation for user {form('username')}")
        pv = PasswordValidator(password_lists=Path("./wordlists/"))
        pv.validate(form('new-password'))
        LOG.info(f"password was successfully validated for user {form('username')}")

    except PasswordException as e:
        return error(str(e))

    try:
        change_password(form('username'), form('old-password'), form('new-password'))
    except Error as e:
        LOG.warning("Unsuccessful attempt to change password for %s: %s" % (form('username'), e))
        return error(str(e))

    LOG.info("Password successfully changed for: %s" % form('username'))

    return index_tpl(alerts=[('success', "Password has been changed")])


@route('/static/<filename>', name='static')
def serve_static(filename):
    return static_file(filename, root=path.join(BASE_DIR, 'static'))


def index_tpl(**kwargs):
    return template('index', **kwargs)


def connect_ldap(conf, **kwargs):
    tls = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLS, ca_certs_file=conf['ca_cert'])
    server = Server(host=conf['host'],
                    port=conf.getint('port', None),
                    tls=tls,
                    get_info=ALL,
                    connect_timeout=5)

    connection = Connection(server, authentication=SIMPLE, raise_exceptions=True, **kwargs)
    connection.start_tls()
    return connection


def change_password(username, old_pass, new_pass):
    try:
        change_password_ldap(CONF["ldap"], username, old_pass, new_pass)

    except (LDAPBindError, LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError):
        raise Error('Username or password is incorrect!')

    except LDAPConstraintViolationResult as e:
        # Extract useful part of the error message (for Samba 4 / AD).
        msg = e.message.split('check_password_restrictions: ')[-1].capitalize()
        raise Error(msg)

    except LDAPSocketOpenError as e:
        LOG.error('{}: {!s}'.format(e.__class__.__name__, e))
        raise Error('Unable to connect to the remote server.')

    except LDAPExceptionError as e:
        LOG.error('{}: {!s}'.format(e.__class__.__name__, e))
        raise Error('Encountered an unexpected error while communicating with the remote server.')


def change_password_ldap(conf, username, old_pass, new_pass):
    with connect_ldap(conf, user=conf.get('search_user_dn'), password=conf.get('search_user_password')) as c:
        user_dn = find_user_dn(conf, c, username)

    # Note: raises LDAPUserNameIsMandatoryError when user_dn is None.
    with connect_ldap(conf, user=user_dn, password=old_pass) as c:
        c.bind()
        c.extend.standard.modify_password(user_dn, old_pass, new_pass)


def find_user_dn(conf, conn, uid):
    search_filter = conf['search_filter'].replace('{uid}', uid)
    conn.search(conf['base'], "(%s)" % search_filter, SUBTREE)
    return conn.response[0]['dn'] if conn.response else None


def read_config():
    config = ConfigParser()
    config.read([path.join(BASE_DIR, 'settings.ini'), os.getenv('CONF_FILE', '')])
    return config


class Error(Exception):
    pass


if environ.get('DEBUG'):
    bottle.debug(True)

# Set up logging.
logging.basicConfig(format=LOG_FORMAT)
LOG.setLevel(logging.INFO)
LOG.info("Starting ldap-passwd-webui %s" % VERSION)

CONF = read_config()

bottle.TEMPLATE_PATH = [BASE_DIR]

# Set default attributes to pass into templates.
SimpleTemplate.defaults = dict(CONF['html'])
SimpleTemplate.defaults['url'] = bottle.url

# Run bottle internal server when invoked directly (mainly for development).
if __name__ == '__main__':
    bottle.run(**CONF['server'])
# Run bottle in application mode (in production under uWSGI server).
else:
    LOG.info("initialize new password validator")
    pv = PasswordValidator(password_lists=Path("./wordlists/"))
    LOG.info(f"New password validator initialized with {pv.get_known_passwords_amount()} known passwords.")
    application = bottle.default_app()
