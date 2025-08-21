"""
Signal handlers for issues app
"""

import json
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Issue
from .integrations import notify_slack


logger = logging.getLogger('issues')


@receiver(post_save, sender=Issue)
def issue_created(sender, instance, created, **kwargs):
    """Signal handler for when an issue is created"""
    if created:
        # Send Slack notification for new issues
        notify_slack(instance)
        
        # Log issue creation
        logger.info(json.dumps({
            "event": "issue_created", 
            "issue_id": instance.id, 
            "summary": instance.summary,
            "author": instance.author.email
        }))