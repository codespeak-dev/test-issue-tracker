import atexit
import logging
from django.apps import AppConfig

logger = logging.getLogger('bugger')


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Log server startup
        logger.info('"Server started successfully"')
        
        # Register shutdown handler
        def shutdown_handler():
            logger.info('"Stopping server"')
        
        atexit.register(shutdown_handler)
