from django.apps import AppConfig
import sys
import os

class MoviesConfig(AppConfig):
    name = 'movies'

    def ready(self):
        import movies.signals
        
        # Prevent scheduler from running multiple times or during migrations
        if os.environ.get('RUN_MAIN', None) != 'true' and 'runserver' not in sys.argv:
            return
            
        from . import scheduler
        scheduler.start()
