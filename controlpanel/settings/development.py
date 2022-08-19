from controlpanel.settings.common import *

# Enable debugging
DEBUG = True

# Allow all hostnames to access the server
ALLOWED_HOSTS = "*"

# Install the develop pages in development mode
INSTALLED_APPS.append("controlpanel.develop")

# Enable Django debug toolbar
if os.environ.get("ENABLE_DJANGO_DEBUG_TOOLBAR"):
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INSTALLED_APPS.extend(
        ["debug_toolbar", "requests_toolbar", "elastic_panel"]
    )
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        # Jinja2 not supported
        # 'debug_toolbar.panels.templates.TemplatesPanel',
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "requests_toolbar.panels.RequestsDebugPanel",
        "elastic_panel.panel.ElasticDebugPanel",
    ]

INTERNAL_IPS = ["127.0.0.1"]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# -- Structured logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.KeyValueRenderer(key_order=['timestamp', 'level', 'event', 'logger']),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
        },
    },
    "loggers": {
        "django_structlog": {
            "handlers": ["console", ],
            "level": "INFO",
        },
        # Make sure to replace the following logger's name for yours
        "controlpanel": {
            "handlers": ["console", ],
            "level": "INFO",
        },
    }
}