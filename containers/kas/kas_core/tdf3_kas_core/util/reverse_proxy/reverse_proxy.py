import logging

logger = logging.getLogger(__name__)


class ReverseProxied(object):
    # More about this pattern
    # https://github.com/spec-first/connexion/tree/main/examples/openapi3/reverseproxy
    def __init__(self, app, script_name=None, scheme=None, server=None):
        self.app = app
        self.script_name = script_name
        self.scheme = scheme
        self.server = server

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_FORWARDED_PATH", "") or self.script_name
        if script_name:
            environ["SCRIPT_NAME"] = "/" + script_name.lstrip("/")
            path_info = environ["PATH_INFO"]
            if path_info.startswith(script_name):
                environ["PATH_INFO_OLD"] = path_info
                environ["PATH_INFO"] = path_info[len(script_name) :]
        scheme = environ.get("HTTP_X_SCHEME", "") or self.scheme
        if scheme:
            environ["wsgi.url_scheme"] = scheme
        server = environ.get("HTTP_X_FORWARDED_SERVER", "") or self.server
        if server:
            environ["HTTP_HOST"] = server
        return self.app(environ, start_response)
