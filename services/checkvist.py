"""
Checkvist API Service for py_home

Task management integration with Checkvist.

Setup:
1. Get API credentials:
   - Login to https://checkvist.com
   - Go to Settings → API
   - Note your username and API key
2. Add to config/.env:
   - CHECKVIST_USERNAME=your@email.com
   - CHECKVIST_API_KEY=your_api_key
3. Configure lists in config/config.yaml

API Docs: https://checkvist.com/auth/api
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CheckvistAPI:
    """
    Checkvist API client for task management

    Supports creating tasks in different lists (work, personal, etc.)
    """

    BASE_URL = "https://checkvist.com"

    def __init__(self, username=None, api_key=None):
        from lib.config import config

        self.username = username or config['checkvist']['username']
        self.api_key = api_key or config['checkvist']['api_key']

        if not self.username or not self.api_key:
            raise ValueError(
                "Checkvist credentials not configured. "
                "Add CHECKVIST_USERNAME and CHECKVIST_API_KEY to config/.env"
            )

        self.auth = (self.username, self.api_key)

    def _get(self, endpoint, params=None):
        """Make GET request to Checkvist API"""
        url = f"{self.BASE_URL}{endpoint}.json"
        resp = requests.get(url, auth=self.auth, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint, data=None):
        """Make POST request to Checkvist API"""
        url = f"{self.BASE_URL}{endpoint}.json"
        resp = requests.post(url, auth=self.auth, json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_lists(self):
        """
        Get all checklists

        Returns:
            list: List of checklists with id, name, and item counts
        """
        endpoint = "/checklists"
        lists = self._get(endpoint)

        result = []
        for lst in lists:
            result.append({
                'id': lst['id'],
                'name': lst['name'],
                'public': lst['public'],
                'item_count': lst['task_count'],
                'completed_count': lst['task_completed']
            })

        logger.info(f"Retrieved {len(result)} Checkvist lists")
        return result

    def add_task(self, list_id, task_text, due_date=None, tags=None):
        """
        Add task to a checklist

        Args:
            list_id: Checklist ID (int)
            task_text: Task description
            due_date: Optional due date (YYYY-MM-DD format)
            tags: Optional list of tags

        Returns:
            dict: Created task information

        Example:
            >>> api = CheckvistAPI()
            >>> api.add_task(123456, "Review PR #42", tags=["coding"])
        """
        endpoint = f"/checklists/{list_id}/tasks"

        data = {
            'task': {
                'content': task_text
            }
        }

        if due_date:
            data['task']['due'] = due_date

        if tags:
            # Checkvist uses #tags in the content
            tag_str = ' ' + ' '.join(f'#{tag}' for tag in tags)
            data['task']['content'] += tag_str

        result = self._post(endpoint, data)

        logger.info(f"Added task to list {list_id}: {task_text}")

        return {
            'status': 'success',
            'task_id': result['id'],
            'content': result['content'],
            'list_id': list_id
        }

    def add_task_by_list_name(self, list_name, task_text, due_date=None, tags=None):
        """
        Add task to a checklist by name

        Args:
            list_name: Checklist name (e.g., "work", "personal")
            task_text: Task description
            due_date: Optional due date
            tags: Optional list of tags

        Returns:
            dict: Created task information

        Example:
            >>> api = CheckvistAPI()
            >>> api.add_task_by_list_name("work", "Review PR #42")
        """
        from lib.config import config

        # Get list ID from config
        lists_config = config['checkvist']['lists']

        if list_name not in lists_config:
            raise ValueError(f"List '{list_name}' not configured in config.yaml")

        list_id = lists_config[list_name]

        return self.add_task(list_id, task_text, due_date, tags)

    def get_tasks(self, list_id, status='open'):
        """
        Get tasks from a checklist

        Args:
            list_id: Checklist ID
            status: 'open', 'closed', or 'all'

        Returns:
            list: Tasks
        """
        endpoint = f"/checklists/{list_id}/tasks"

        params = {}
        if status == 'open':
            params['status'] = '0'  # 0 = open
        elif status == 'closed':
            params['status'] = '1'  # 1 = closed

        tasks = self._get(endpoint, params)

        result = []
        for task in tasks:
            result.append({
                'id': task['id'],
                'content': task['content'],
                'status': task['status'],  # 0 = open, 1 = closed
                'due': task.get('due'),
                'position': task['position']
            })

        logger.info(f"Retrieved {len(result)} tasks from list {list_id}")
        return result


# Singleton instance
_checkvist = None

def get_checkvist():
    """Get or create Checkvist API instance"""
    global _checkvist
    if _checkvist is None:
        _checkvist = CheckvistAPI()
    return _checkvist


# Convenience functions
def add_task(list_name, task_text, due_date=None, tags=None):
    """Add task to checklist by name"""
    return get_checkvist().add_task_by_list_name(list_name, task_text, due_date, tags)


def get_lists():
    """Get all checklists"""
    return get_checkvist().get_lists()


__all__ = [
    'CheckvistAPI',
    'get_checkvist',
    'add_task',
    'get_lists'
]
