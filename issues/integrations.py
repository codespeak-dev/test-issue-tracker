"""
External API integrations (Slack and GitHub)
"""

import logging
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


logger = logging.getLogger('issues')


def notify_slack(issue):
    """Send a Slack notification when a new issue is created"""
    if not settings.SLACK_BOT_TOKEN or not settings.SLACK_CHANNEL_ID:
        logger.info("Slack integration not configured, skipping notification")
        return
    
    try:
        client = WebClient(token=settings.SLACK_BOT_TOKEN)
        
        message = f"🐛 New issue created: *{issue.summary}*\n" \
                 f"Author: {issue.author.name}\n" \
                 f"Status: {issue.status.name}\n" \
                 f"View: http://localhost:8000{issue.get_absolute_url()}"
        
        result = client.chat_postMessage(
            channel=settings.SLACK_CHANNEL_ID,
            text=message
        )
        
        if result["ok"]:
            logger.info(f"Slack notification sent for issue {issue.id}")
        else:
            logger.error(f"Failed to send Slack notification: {result}")
            
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}")