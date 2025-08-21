"""
Configuration validation module for external APIs.

This module validates that external API configurations are set correctly
by making simple read requests to each API using their respective SDKs.
"""

import os
import sys
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from github import Github
from github.GithubException import GithubException


def load_configuration() -> Dict[str, str]:
    """Load configuration from .env.local file."""
    env_path = ".env.local"
    if not os.path.exists(env_path):
        print(f"❌ Configuration file '{env_path}' not found!")
        print(f"Please create the file with your API configuration parameters.")
        sys.exit(1)
    
    load_dotenv(env_path)
    
    config = {
        "slack_bot_token": os.getenv("SLACK_BOT_TOKEN"),
        "slack_channel_id": os.getenv("SLACK_CHANNEL_ID"), 
        "github_access_token": os.getenv("GITHUB_ACCESS_TOKEN"),
        "github_repository_owner": os.getenv("GITHUB_REPOSITORY_OWNER"),
        "github_repository_name": os.getenv("GITHUB_REPOSITORY_NAME")
    }
    
    return config


def validate_slack_configuration(config: Dict[str, str]) -> Tuple[bool, str, Dict]:
    """
    Validate Slack configuration by making a simple API call.
    
    Returns:
        Tuple of (success, error_message, details)
    """
    slack_bot_token = config.get("slack_bot_token")
    slack_channel_id = config.get("slack_channel_id")
    
    if not slack_bot_token:
        return False, "SLACK_BOT_TOKEN is not set", {}
    
    if not slack_channel_id:
        return False, "SLACK_CHANNEL_ID is not set", {}
    
    # Extract channel ID if it's a full URL
    if slack_channel_id.startswith("https://"):
        if "/archives/" in slack_channel_id:
            slack_channel_id = slack_channel_id.split("/archives/")[-1]
        else:
            return False, "SLACK_CHANNEL_ID appears to be a URL but doesn't contain '/archives/'", {"provided_value": slack_channel_id}
    
    client = WebClient(token=slack_bot_token)
    
    try:
        # Test bot token validity by calling auth.test
        auth_response = client.auth_test()
        
        # Test channel access by getting channel info
        channel_response = client.conversations_info(channel=slack_channel_id)
        
        details = {
            "bot_user_id": auth_response.get("user_id"),
            "bot_name": auth_response.get("user"),
            "team_name": auth_response.get("team"),
            "channel_name": channel_response.get("channel", {}).get("name"),
            "channel_id": slack_channel_id
        }
        
        return True, "Slack configuration validated successfully", details
        
    except SlackApiError as e:
        error_code = e.response["error"]
        details = {
            "error_code": error_code,
            "response": e.response,
            "token_prefix": slack_bot_token[:10] + "..." if slack_bot_token else None,
            "channel_id": slack_channel_id
        }
        
        if error_code == "invalid_auth":
            return False, "Invalid Slack bot token", details
        elif error_code == "channel_not_found":
            return False, "Slack channel not found or bot doesn't have access", details
        else:
            return False, f"Slack API error: {error_code}", details
    
    except Exception as e:
        return False, f"Unexpected error validating Slack configuration: {str(e)}", {"exception": str(e)}


def validate_github_configuration(config: Dict[str, str]) -> Tuple[bool, str, Dict]:
    """
    Validate GitHub configuration by making a simple API call.
    
    Returns:
        Tuple of (success, error_message, details)
    """
    github_access_token = config.get("github_access_token")
    github_repository_owner = config.get("github_repository_owner")
    github_repository_name = config.get("github_repository_name")
    
    if not github_access_token:
        return False, "GITHUB_ACCESS_TOKEN is not set", {}
    
    if not github_repository_owner:
        return False, "GITHUB_REPOSITORY_OWNER is not set", {}
    
    if not github_repository_name:
        return False, "GITHUB_REPOSITORY_NAME is not set", {}
    
    github_client = Github(github_access_token)
    
    try:
        # Test token validity by getting authenticated user
        user = github_client.get_user()
        
        # Test repository access
        repo = github_client.get_repo(f"{github_repository_owner}/{github_repository_name}")
        
        details = {
            "authenticated_user": user.login,
            "repository_full_name": repo.full_name,
            "repository_owner": github_repository_owner,
            "repository_name": github_repository_name,
            "repository_private": repo.private,
            "repository_default_branch": repo.default_branch
        }
        
        return True, "GitHub configuration validated successfully", details
        
    except GithubException as e:
        details = {
            "status_code": e.status,
            "data": e.data,
            "token_prefix": github_access_token[:10] + "..." if github_access_token else None,
            "repository_path": f"{github_repository_owner}/{github_repository_name}"
        }
        
        if e.status == 401:
            return False, "Invalid GitHub access token or insufficient permissions", details
        elif e.status == 404:
            return False, "GitHub repository not found or no access permissions", details
        else:
            return False, f"GitHub API error (status {e.status}): {e.data.get('message', 'Unknown error')}", details
    
    except Exception as e:
        return False, f"Unexpected error validating GitHub configuration: {str(e)}", {"exception": str(e)}


def validate_configuration():
    """
    Main function to validate all external API configurations.
    This function is called by the CLI command.
    """
    print("🔍 Validating external API configurations...")
    print()
    
    # Load configuration
    try:
        config = load_configuration()
    except SystemExit:
        return  # load_configuration already printed error and called sys.exit
    
    checks = [
        ("Slack", validate_slack_configuration),
        ("GitHub", validate_github_configuration)
    ]
    
    all_passed = True
    results = []
    
    for api_name, validation_func in checks:
        print(f"Checking {api_name} configuration...")
        success, message, details = validation_func(config)
        results.append((api_name, success, message, details))
        
        if success:
            print(f"  ✅ {message}")
            if details:
                for key, value in details.items():
                    if key not in ["token_prefix"]:  # Don't print sensitive info
                        print(f"     • {key}: {value}")
        else:
            print(f"  ❌ {message}")
            all_passed = False
            if details:
                print("     Details:")
                for key, value in details.items():
                    print(f"     • {key}: {value}")
        print()
    
    # Summary
    passed_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)
    
    print("=" * 50)
    if all_passed:
        print(f"🎉 All {total_count} configuration checks passed!")
        print("Your external API configurations are working correctly.")
    else:
        failed_count = total_count - passed_count
        print(f"⚠️  {passed_count}/{total_count} configuration checks passed.")
        print(f"   {failed_count} check(s) failed.")
        print()
        print("Please fix the failed configurations and run this command again.")
        sys.exit(1)


if __name__ == "__main__":
    validate_configuration()