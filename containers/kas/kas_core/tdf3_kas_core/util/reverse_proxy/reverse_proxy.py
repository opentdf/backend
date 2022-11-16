import logging

logger = logging.getLogger(__name__)


class ReverseProxied(object):
    """Wrap the application in this middleware and configure the
    #     reverse proxy to add these headers, to let you quietly bind
    #     this to a URL other than / and to an HTTP scheme that is
    #     different than what is used locally.
    #     In nginx:
    #     location /proxied {
    #         proxy_pass http://192.168.0.1:5001;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Scheme $scheme;
    #         proxy_set_header X-Forwarded-Path /proxied;
    #     }
    #     :param app: the WSGI application
    #     :param script_name: override the default script name (path)
    #     :param scheme: override the default scheme
    #     :param server: override the default server
    #"""

    def __init__(self, app, script_name=None, scheme=None, server=None):
        self.app = app
        self.script_name = script_name
        self.scheme = scheme
        self.server = server

    def __call__(self, environ, start_response):
        logging.warning(
            "this demo is not secure by default!! "
            "You'll want to make sure these headers are coming from your proxy, "
            "and not directly from users on the web!"
        )
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


# class ReverseProxied(object):
#     '''Wrap the application in this middleware and configure the
#     reverse proxy to add these headers, to let you quietly bind
#     this to a URL other than / and to an HTTP scheme that is
#     different than what is used locally.
#     In nginx:
#     location /proxied {
#         proxy_pass http://192.168.0.1:5001;
#         proxy_set_header Host $host;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Scheme $scheme;
#         proxy_set_header X-Forwarded-Path /proxied;
#     }
#     :param app: the WSGI application
#     :param script_name: override the default script name (path)
#     :param scheme: override the default scheme
#     :param server: override the default server
#     '''
#
#     def __init__(self, app, script_name=None, scheme=None, server=None):
#         self.app = app
#         self.script_name = script_name
#         self.scheme = scheme
#         self.server = server
#
#     def __call__(self, environ, start_response):
#         logging.warning(
#             "this demo is not secure by default!! "
#             "You'll want to make sure these headers are coming from your proxy, "
#             "and not directly from users on the web!"
#         )
#         script_name = environ.get('HTTP_X_FORWARDED_PATH', '') or self.script_name
#         if script_name:
#             environ['SCRIPT_NAME'] = "/" + script_name.lstrip("/")
#             path_info = environ['PATH_INFO']
#             if path_info.startswith(script_name):
#                 environ['PATH_INFO_OLD'] = path_info
#                 environ['PATH_INFO'] = path_info[len(script_name):]
#         scheme = environ.get('HTTP_X_SCHEME', '') or self.scheme
#         if scheme:
#             environ['wsgi.url_scheme'] = scheme
#         server = environ.get('HTTP_X_FORWARDED_SERVER', '') or self.server
#         if server:
#             environ['HTTP_HOST'] = server
#         return self.app(environ, start_response)
