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
        return None
    
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
            return result["ts"]  # Return thread timestamp
        else:
            logger.error(f"Failed to send Slack notification: {result}")
            return None
            
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}")
        return None


def notify_slack_comment(comment):
    """Send a Slack notification when a comment is added to an issue"""
    if not settings.SLACK_BOT_TOKEN or not settings.SLACK_CHANNEL_ID:
        logger.info("Slack integration not configured, skipping comment notification")
        return
    
    # Only send comment notification if we have a thread timestamp from the original issue
    if not comment.issue.slack_thread_ts:
        logger.info(f"No Slack thread timestamp found for issue {comment.issue.id}, skipping comment notification")
        return
    
    try:
        client = WebClient(token=settings.SLACK_BOT_TOKEN)
        
        message = f"💬 New comment by {comment.author.name}:\n{comment.content[:200]}{'...' if len(comment.content) > 200 else ''}"
        
        result = client.chat_postMessage(
            channel=settings.SLACK_CHANNEL_ID,
            thread_ts=comment.issue.slack_thread_ts,
            text=message
        )
        
        if result["ok"]:
            logger.info(f"Slack comment notification sent for comment {comment.id} on issue {comment.issue.id}")
        else:
            logger.error(f"Failed to send Slack comment notification: {result}")
            
    except SlackApiError as e:
        logger.error(f"Slack API error sending comment notification: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending Slack comment notification: {e}")