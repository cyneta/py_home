"""
GitHub API Service for py_home

Commit tasks to TODO.md via voice/iOS Shortcuts.

Setup:
1. Create GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Generate new token (classic)
   - Scope: 'repo' (full control of private repositories)
2. Add to config/.env: GITHUB_TOKEN=your_token
3. Configure repo in config/config.yaml

API Docs: https://docs.github.com/en/rest
"""

import requests
import logging
import base64
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubAPI:
    """
    GitHub API client for committing to repositories

    Allows voice-to-commit workflow for task capture.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token=None, repo=None):
        from lib.config import config

        self.token = token or config['github']['token']
        self.repo = repo or config['github']['repo']  # Format: "username/repo"

        if not self.token:
            raise ValueError(
                "GitHub token not configured. "
                "Add GITHUB_TOKEN to config/.env"
            )

        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def _get(self, endpoint):
        """Make GET request to GitHub API"""
        url = f"{self.BASE_URL}{endpoint}"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _put(self, endpoint, data):
        """Make PUT request to GitHub API"""
        url = f"{self.BASE_URL}{endpoint}"
        resp = requests.put(url, json=data, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_file_contents(self, path, branch='main'):
        """
        Get file contents from repository

        Args:
            path: File path in repo (e.g., "TODO.md")
            branch: Branch name (default: main)

        Returns:
            dict: {
                'content': str (decoded file content),
                'sha': str (file SHA for updates)
            }
        """
        endpoint = f"/repos/{self.repo}/contents/{path}"
        params = {'ref': branch}

        url = f"{self.BASE_URL}{endpoint}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()

        # Decode base64 content
        content = base64.b64decode(data['content']).decode('utf-8')

        return {
            'content': content,
            'sha': data['sha']
        }

    def update_file(self, path, content, message, branch='main', sha=None):
        """
        Update file in repository

        Args:
            path: File path in repo
            content: New file content (string)
            message: Commit message
            branch: Branch name
            sha: Current file SHA (required for updates)

        Returns:
            dict: Commit information
        """
        endpoint = f"/repos/{self.repo}/contents/{path}"

        # Encode content to base64
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        data = {
            'message': message,
            'content': content_base64,
            'branch': branch
        }

        if sha:
            data['sha'] = sha

        result = self._put(endpoint, data)

        logger.info(f"Updated {path} in {self.repo}: {message}")
        return result

    def add_task_to_todo(self, task_text):
        """
        Add task to TODO.md file

        Args:
            task_text: Task description

        Returns:
            dict: Commit information

        Example:
            >>> github = GitHubAPI()
            >>> github.add_task_to_todo("Fix the leaky faucet")
        """
        from lib.config import config

        todo_path = config['github']['todo_path']

        try:
            # Get current TODO.md contents
            file_data = self.get_file_contents(todo_path)
            current_content = file_data['content']
            sha = file_data['sha']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # File doesn't exist, create it
                current_content = "# TODO\n\n"
                sha = None
            else:
                raise

        # Add new task with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_task = f"- [ ] {task_text} (added {timestamp})\n"

        # Append to file
        new_content = current_content + new_task

        # Commit
        commit_message = f"Add task: {task_text}"
        result = self.update_file(todo_path, new_content, commit_message, sha=sha)

        logger.info(f"Added task to TODO.md: {task_text}")

        return {
            'status': 'success',
            'task': task_text,
            'commit': result['commit']['sha'][:7],
            'url': result['commit']['html_url']
        }

    def get_repo_info(self):
        """
        Get repository information

        Returns:
            dict: Repository details
        """
        endpoint = f"/repos/{self.repo}"
        data = self._get(endpoint)

        return {
            'name': data['name'],
            'full_name': data['full_name'],
            'description': data['description'],
            'url': data['html_url'],
            'default_branch': data['default_branch']
        }


# Singleton instance
_github = None

def get_github():
    """Get or create GitHub API instance"""
    global _github
    if _github is None:
        _github = GitHubAPI()
    return _github


# Convenience functions
def add_task(task_text):
    """Add task to TODO.md"""
    return get_github().add_task_to_todo(task_text)


def get_repo_info():
    """Get repository information"""
    return get_github().get_repo_info()


__all__ = [
    'GitHubAPI',
    'get_github',
    'add_task',
    'get_repo_info'
]
