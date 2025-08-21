"""
Django management command for polling GitHub repository for commits that close issues.
"""

import re
import time
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from django.core.management.base import BaseCommand
from django.utils import timezone
from github import Github
from github.GithubException import GithubException
from issues.models import Issue, Comment, Settings, Status


logger = logging.getLogger('issues')


class Command(BaseCommand):
    help = 'Poll GitHub repository for commits that close issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Polling interval in seconds (default: 10)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once instead of continuous polling'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        self.stdout.write(f"Starting GitHub poller (interval: {interval}s)")
        logger.info(f"GitHub poller started with interval {interval}s")
        
        while True:
            try:
                self.poll_github()
                
                if run_once:
                    break
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.stdout.write("GitHub poller stopped by user")
                logger.info("GitHub poller stopped by user")
                break
            except Exception as e:
                error_msg = f"Error in GitHub poller: {str(e)}"
                self.stderr.write(self.style.ERROR(error_msg))
                logger.error(error_msg)
                
                if run_once:
                    break
                    
                time.sleep(interval)
    
    def poll_github(self):
        """Poll GitHub for new commits and process issue closures"""
        settings = Settings.load()
        
        if not all([
            settings.github_access_token,
            settings.github_repository_owner,
            settings.github_repository_name
        ]):
            self.stdout.write("GitHub integration not configured, skipping poll")
            return
        
        try:
            # Initialize GitHub client
            github_client = Github(settings.github_access_token)
            repo = github_client.get_repo(
                f"{settings.github_repository_owner}/{settings.github_repository_name}"
            )
            
            # Get commits from the last 24 hours
            since_time = timezone.now() - timedelta(hours=24)
            commits = repo.get_commits(since=since_time)
            
            processed_count = 0
            
            for commit in commits:
                if self.process_commit(commit):
                    processed_count += 1
            
            if processed_count > 0:
                self.stdout.write(f"Processed {processed_count} issue-closing commits")
                logger.info(f"Processed {processed_count} issue-closing commits")
            
        except GithubException as e:
            error_msg = f"GitHub API error: {e.status} - {e.data.get('message', 'Unknown error')}"
            self.stderr.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error polling GitHub: {str(e)}"
            self.stderr.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
    
    def process_commit(self, commit):
        """Process a single commit and close issues if pattern matches"""
        commit_message = commit.commit.message
        
        # Look for pattern: #<issue-id> Fixed
        pattern = r'#(\d+)\s+Fixed'
        matches = re.findall(pattern, commit_message, re.IGNORECASE)
        
        processed = False
        
        for issue_id_str in matches:
            try:
                issue_id = int(issue_id_str)
                issue = Issue.objects.get(id=issue_id)
                
                # Skip if issue is already closed
                if not issue.status.is_open:
                    continue
                
                # Close the issue
                done_status = Status.objects.filter(name='Done').first()
                if done_status:
                    issue.status = done_status
                    issue.save()
                    
                    # Add comment with commit info
                    comment_content = (
                        f"🎉 **Issue automatically closed by commit**\n\n"
                        f"**Commit:** [{commit.sha[:8]}]({commit.html_url})\n"
                        f"**Author:** {commit.commit.author.name}\n"
                        f"**Message:** {commit_message.strip()}\n"
                        f"**Date:** {commit.commit.author.date.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                    
                    # Find or create a system user for automated comments
                    from issues.models import User
                    system_user, created = User.objects.get_or_create(
                        email='system@bugger.local',
                        defaults={'name': 'Bugger System'}
                    )
                    
                    Comment.objects.create(
                        content=comment_content,
                        author=system_user,
                        issue=issue
                    )
                    
                    success_msg = f"Closed issue #{issue_id} due to commit {commit.sha[:8]}"
                    self.stdout.write(self.style.SUCCESS(success_msg))
                    logger.info(success_msg)
                    
                    processed = True
                else:
                    error_msg = f"Could not find 'Done' status to close issue #{issue_id}"
                    self.stderr.write(self.style.WARNING(error_msg))
                    logger.warning(error_msg)
                    
            except Issue.DoesNotExist:
                error_msg = f"Issue #{issue_id_str} not found in commit {commit.sha[:8]}"
                self.stderr.write(self.style.WARNING(error_msg))
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Error processing issue #{issue_id_str} from commit {commit.sha[:8]}: {str(e)}"
                self.stderr.write(self.style.ERROR(error_msg))
                logger.error(error_msg)
        
        return processed