"""The KAS class builds the Flask app from openapi.yaml using Connexion."""

import os
import connexion
import importlib_resources
import logging
import urllib.parse

from . import services

from .models import HealthzPluginRunner
from .models import RewrapPluginRunner
from .models import RewrapPluginRunnerV2
from .models import UpsertPluginRunner
from .models import UpsertPluginRunnerV2
from .models import KeyMaster

from .errors import PluginIsBadError
from .errors import ServerStartupError
from .errors import MiddlewareIsBadError

from .abstractions import (
    AbstractHealthzPlugin,
    AbstractRewrapPlugin,
    AbstractUpsertPlugin,
)

from .util.utility import value_to_boolean
from .util.reverse_proxy import ReverseProxied
from .util.swagger_ui_bundle import swagger_ui_4_path
from .util.hooks import hook_into, post_rewrap_v2_hook_default

logger = logging.getLogger(__name__)


def clean_trusted_url(u):
    r = urllib.parse.urlparse(u, scheme="https")
    if r.fragment:
        logger.warning(
            "Fragments in trusted entitlement URIs are ignored: [%s] won't be required",
            r.fragment,
        )
    if r.query:
        logger.warning(
            "Be careful. We use prefix matching for trusted entitlers, so query params are unusual [%s]",
            u,
        )
        if r.path:
            return f"{r.scheme}://{r.netloc}{r.path}?{r.query}"
        return f"{r.scheme}://{r.netloc}/?{r.query}"
    if not r.path:
        return f"{r.scheme}://{r.netloc}/"
    return f"{r.scheme}://{r.netloc}{r.path}"


def create_session_ping(version):
    """Create a session ping callable."""

    def session_ping(request=None):
        return services.ping(version)

    return session_ping


def create_session_healthz(plugins):
    """Wrapper for healthz plugins"""
    plugin_runner = HealthzPluginRunner(plugins)

    def session_healthz(*, probe="liveness"):
        plugin_runner.healthz(probe=probe)

    return session_healthz


def create_session_rewrap(key_master, plugins):
    """Create a simpler callable that accepts one argument, the data.

    The other components that the rewrap service needs are captured in the
    closure of this factory function.  This pre-loaded dependency injection
    makes the service call cleaner and clearer.
    """
    plugin_runner = RewrapPluginRunner(plugins)

    def session_rewrap(data, options):
        return services.rewrap(data, options, plugin_runner, key_master)

    return session_rewrap


def create_session_rewrap_v2(key_master, plugins, trusted_entitlers):
    """Create a simpler callable that accepts one argument, the data.

    The other components that the rewrap service needs are captured in the
    closure of this factory function.  This pre-loaded dependency injection
    makes the service call cleaner and clearer.
    """
    plugin_runner = RewrapPluginRunnerV2(plugins)

    def session_rewrap(data, options):
        return hook_into(
            post=Kas.get_instance()._post_rewrap_hook,
            err=Kas.get_instance()._err_rewrap_hook,
        )(services.rewrap_v2)(
            data, options, plugin_runner, key_master, trusted_entitlers
        )

    return session_rewrap


def create_session_upsert(key_master, plugins):
    """Create a simpler callable that accepts one argument, the data.

    The other components that the upsert service needs are captured in the
    closure of this factory function.  This pre-loaded dependency injection
    makes the service call cleaner and clearer.
    """
    plugin_runner = UpsertPluginRunner(plugins)

    def session_upsert(data, options):
        return services.upsert(data, options, plugin_runner, key_master)

    return session_upsert


def create_session_upsert_v2(key_master, plugins, trusted_entitlers):
    """Create a simpler callable that accepts one argument, the data.

    The other components that the upsert service needs are captured in the
    closure of this factory function.  This pre-loaded dependency injection
    makes the service call cleaner and clearer.

    (narrator voice: "Translation: 'I made this one aspect simpler at the cost of making LITERALLY EVERYTHING ELSE MORE COMPLICATED'")
    """
    plugin_runner = UpsertPluginRunnerV2(plugins)

    def session_upsert(data, options):
        return services.upsert_v2(
            data, options, plugin_runner, key_master, trusted_entitlers
        )

    return session_upsert


def create_session_public_key(key_master):
    """Create a session callable for getting the public key.

    The keymaster is carried in the closure of this function.
    """

    def session_kas_public_key(algorithm, fmt, v):
        return services.kas_public_key(key_master, algorithm, fmt, v)

    return session_kas_public_key


class Kas(object):
    """The KAS object is a singleton that contains the business logic callables for the Kas server.

    When the app method is called, Kas will dynamically construct the callables that handle requests.
    For upsert and rewrap, plugins can be loaded to add functionality.
    It will then create the Flask App using Connexion to bind API calls, through web package functions,
    to these callables.
    """

    __instance = None

    @staticmethod
    def get_instance():
        if Kas.__instance == None:
            return Kas()
        return Kas.__instance

    def __init__(self):
        """Construct an empty KAS object with root name."""
        if Kas.__instance != None:
            raise ServerStartupError("Kas App was already created.")
        self._root_name = "kas"
        self._version = "0.0.0"
        self._healthz_plugins = []
        self._rewrap_plugins = []
        self._rewrap_plugins_v2 = []
        self._trusted_entitlers = []
        self._upsert_plugins = []
        self._upsert_plugins_v2 = []
        self._post_rewrap_hook = post_rewrap_v2_hook_default
        self._err_rewrap_hook = lambda *args: None
        self._middleware = None
        self._key_master = KeyMaster()

        # These callables and the flask app will be constructed by the app() method after configuration
        self._session_ping = None
        self._session_rewrap = None
        self._session_rewrap_v2 = None
        self._session_upsert = None
        self._session_upsert_v2 = None
        self._session_kas_public_key = None
        self._app = None

        Kas.__instance = self

    def set_root_name(self, name):
        self._root_name = name

    def set_trusted_entitlers(self, trusted_entitlers):
        self._trusted_entitlers = [clean_trusted_url(e) for e in trusted_entitlers]

    def set_version(self, version=None):
        """Set version for the heartbeat message."""
        if version is not None:
            version = version.strip()  # trim the string
            version = version.rstrip("/n")  # remove linefeed
            logger.debug("Setting version to %s", version)
            self._version = version

    def set_key_pem(self, key_name, key_type, pem_key):
        """Set a key directly with a PEM encoded string."""
        self._key_master.set_key_pem(key_name, key_type, pem_key)

    def set_key_path(self, key_name, key_type, key_path):
        """Set a key by providing a path to a file containing a PEM string."""
        self._key_master.set_key_path(key_name, key_type, key_path)

    def use_upsert_plugin(self, plugin):
        """Add an upsert plugin.

        This method adds policy side-effect plugins to the KAS. The order
        that this method is called in is important. Plugins get the Policy
        returned by the prior plugin. They are called in order.
        """
        if isinstance(plugin, AbstractUpsertPlugin):
            self._upsert_plugins.append(plugin)
        else:
            raise PluginIsBadError("plugin is not a decendent of AbstractUpsertPlugin")

    def use_upsert_plugin_v2(self, plugin):
        """Add an upsert plugin.

        This method adds policy side-effect plugins to the KAS. The order
        that this method is called in is important. Plugins get the Policy
        returned by the prior plugin. They are called in order.
        """
        if isinstance(plugin, AbstractUpsertPlugin):
            self._upsert_plugins_v2.append(plugin)
        else:
            raise PluginIsBadError("plugin is not a decendent of AbstractUpsertPlugin")

    def use_rewrap_plugin(self, plugin):
        """Add a rewrap plugin.

        This method adds policy side-effect plugins to the KAS. The order
        that this method is called in is important. Plugins get the Policy
        returned by the prior plugin. They are called in order.
        """
        if isinstance(plugin, AbstractRewrapPlugin):
            self._rewrap_plugins.append(plugin)
        else:
            raise PluginIsBadError("plugin is not a decendent of AbstractRewrapPlugin")

    def use_rewrap_plugin_v2(self, plugin):
        """Add a rewrap plugin.

        This method adds policy side-effect plugins to the KAS. The order
        that this method is called in is important. Plugins get the Policy
        returned by the prior plugin. They are called in order.
        """
        if isinstance(plugin, AbstractRewrapPlugin):
            self._rewrap_plugins_v2.append(plugin)
        else:
            raise PluginIsBadError("plugin is not a decendent of AbstractRewrapPlugin")

    def use_healthz_plugin(self, plugin):
        """Add a healthz plugin."""
        if isinstance(plugin, AbstractHealthzPlugin):
            self._healthz_plugins.append(plugin)
        else:
            raise PluginIsBadError("plugin is not a decendent of AbstractHealthzPlugin")

    def use_post_rewrap_hook(self, hook):
        """Add a hook called after rewrap completes"""
        if not callable(hook):
            raise MiddlewareIsBadError("Provided error hook is not callable")
        self._post_rewrap_hook = hook

    def use_err_rewrap_hook(self, hook):
        """Add a hook called when rewrap returns an error"""
        if not callable(hook):
            raise MiddlewareIsBadError("Provided error hook is not callable")
        self._err_rewrap_hook = hook

    def add_middleware(self, middleware):
        """add middleware called with upsert and rewrap"""
        if not (callable(middleware) or None):
            raise MiddlewareIsBadError("Provided middleware is not callable")
        self._middleware = middleware

    def get_middleware(self):
        """return the callable middleare"""
        if self._middleware is not None:
            return self._middleware
        return lambda *args: None

    def get_session_healthz(self):
        """return the callable to process healthz requests."""
        return self._session_healthz

    def get_session_ping(self):
        """return the callable to process ping requests."""
        return self._session_ping

    def get_session_rewrap(self):
        """return the callable to process rewrap requests."""
        return self._session_rewrap

    def get_session_rewrap_v2(self):
        """return the callable to process rewrap requests."""
        return self._session_rewrap_v2

    def get_session_upsert(self):
        """return the callable to process upsert requests."""
        return self._session_upsert

    def get_session_upsert_v2(self):
        """return the callable to process upsert requests."""
        return self._session_upsert_v2

    def get_session_public_key(self):
        """return the callable to process public key requests."""
        return self._session_kas_public_key

    def app(self):
        """Produce a wsgi-callable app.

        Build the callables that will be used to process requests.
        Build the Flask app from OpenAPI using Connexion
        The web package is used to connect REST requests to these callables via this Kas object
        """

        if self._app != None:
            raise ServerStartupError("App was already constructed")

        self._session_healthz = create_session_healthz(self._healthz_plugins)

        self._session_ping = create_session_ping(self._version)

        self._session_rewrap = create_session_rewrap(
            self._key_master, self._rewrap_plugins
        )

        self._session_rewrap_v2 = create_session_rewrap_v2(
            self._key_master, self._rewrap_plugins_v2, self._trusted_entitlers
        )

        self._session_upsert = create_session_upsert(
            self._key_master, self._upsert_plugins
        )

        self._session_upsert_v2 = create_session_upsert_v2(
            self._key_master, self._upsert_plugins_v2, self._trusted_entitlers
        )

        self._session_kas_public_key = create_session_public_key(self._key_master)

        flask_options = {"swagger_url": "/docs"}
        app = connexion.FlaskApp(
            self._root_name, specification_dir="api/", options=flask_options
        )

        # Allow swagger_ui to be disabled
        options = {"swagger_ui": False}
        if swagger_enabled():
            # Turn off Swagger UI feature
            logger.warning("Enable Swagger UI")
            flask_app = app.app

            proxied = ReverseProxied(flask_app.wsgi_app, script_name="/api/kas/")
            flask_app.wsgi_app = proxied
            options.update({"swagger_ui": True, "swagger_path": swagger_ui_4_path})
        else:
            logger.debug("Disable Swagger UI")

        # Connexion will link REST endpoints to handlers using the openapi.yaml file
        openapi_file = importlib_resources.files(__package__) / "api" / "openapi.yaml"
        app.add_api(openapi_file, options=options, strict_validation=True)

        logger.debug("KAS app starting.")
        self._app = app.app
        return self._app


def swagger_enabled():
    """Default false, but if SWAGGER_UI env variable is true or 1 then enable"""
    return value_to_boolean(os.getenv("SWAGGER_UI", False))
