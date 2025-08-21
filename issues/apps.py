import atexit
import logging
from django.apps import AppConfig


logger = logging.getLogger('issues')


class IssuesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'issues'
    
    def ready(self):
        """Called when Django starts up"""
        # Log successful server start
        logger.info("Server started successfully")
        
        # Register shutdown handler
        atexit.register(self._shutdown_handler)
        
        # Import signal handlers
        from . import signals
    
    def _shutdown_handler(self):
        """Called when server shuts down"""
        logger.info("Stopping server")