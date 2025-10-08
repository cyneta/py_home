#!/usr/bin/env python
"""
Task Router Automation

Smart routing of tasks based on keywords.

Routes tasks to:
- GitHub (code/project tasks)
- Checkvist work list (work tasks)
- Checkvist personal list (personal tasks)
- Apple Reminders (fallback - returns instruction)

Usage:
    python automations/task_router.py "Fix bug in leaving_home.py"
    python automations/task_router.py "Buy groceries"
    python automations/task_router.py "Review PR #123"
"""

import sys
import logging
import time
import re
from datetime import datetime
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


def classify_task_ai(task_text):
    """
    Classify task using Claude AI

    Args:
        task_text: Task description

    Returns:
        str: 'github', 'work', 'personal', or None if AI unavailable
    """
    api_start = time.time()
    try:
        import anthropic
        import os

        # Get API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            kvlog(logger, logging.WARNING, automation='task_router', action='ai_classify',
                  error_type='ConfigError', error_msg='ANTHROPIC_API_KEY not set')
            return None

        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)

        # Ask Claude to classify
        prompt = f"""Classify this task into ONE category: github, work, or personal.

Task: "{task_text}"

Categories:
- github: Code/development tasks, bug fixes, features, home automation projects
- work: Professional tasks, meetings, emails, client work
- personal: Shopping, errands, appointments, household tasks

Respond with ONLY the category name (github/work/personal), nothing else."""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        classification = message.content[0].text.strip().lower()
        duration_ms = int((time.time() - api_start) * 1000)

        # Validate response
        if classification in ['github', 'work', 'personal']:
            kvlog(logger, logging.INFO, automation='task_router', action='ai_classify',
                  classification=classification, result='ok', duration_ms=duration_ms)
            return classification
        else:
            kvlog(logger, logging.WARNING, automation='task_router', action='ai_classify',
                  error_type='InvalidResponse', error_msg=f'Invalid classification: {classification}',
                  duration_ms=duration_ms)
            return None

    except Exception as e:
        duration_ms = int((time.time() - api_start) * 1000)
        kvlog(logger, logging.WARNING, automation='task_router', action='ai_classify',
              error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
        return None


def classify_task_keywords(task_text):
    """
    Classify task based on keywords (fallback method)

    Args:
        task_text: Task description

    Returns:
        str: 'github', 'work', 'personal', or 'default'
    """
    task_lower = task_text.lower()

    # GitHub keywords (code/project related)
    github_keywords = [
        'fix', 'bug', 'pr', 'pull request', 'commit', 'merge',
        'code', 'py_home', 'siri_n8n', 'component', 'script',
        'refactor', 'test', 'debug', 'implement', 'feature'
    ]

    # Work keywords
    work_keywords = [
        'meeting', 'email', 'report', 'presentation', 'deadline',
        'client', 'project', 'review', 'call', 'schedule'
    ]

    # Personal keywords
    personal_keywords = [
        'buy', 'groceries', 'clean', 'laundry', 'appointment',
        'doctor', 'dentist', 'car', 'bills', 'errands'
    ]

    # Check for GitHub patterns
    if re.search(r'#\d+', task_text):  # PR/issue number
        return 'github'

    for keyword in github_keywords:
        if keyword in task_lower:
            return 'github'

    # Check for work keywords
    for keyword in work_keywords:
        if keyword in task_lower:
            return 'work'

    # Check for personal keywords
    for keyword in personal_keywords:
        if keyword in task_lower:
            return 'personal'

    # Default to personal
    return 'personal'


def classify_task(task_text, use_ai=True):
    """
    Classify task using AI (preferred) or keywords (fallback)

    Args:
        task_text: Task description
        use_ai: Try AI classification first (default: True)

    Returns:
        str: 'github', 'work', or 'personal'
    """
    if use_ai:
        # Try AI classification first
        ai_result = classify_task_ai(task_text)
        if ai_result:
            return ai_result

    # Fall back to keyword classification
    kvlog(logger, logging.INFO, automation='task_router', action='classify',
          method='keywords')
    return classify_task_keywords(task_text)


def run(task_text):
    """
    Route task to appropriate system

    Args:
        task_text: Task description

    Returns:
        dict: Routing result
    """
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    kvlog(logger, logging.NOTICE, automation='task_router', event='start', task=task_text)

    classification = classify_task(task_text)
    kvlog(logger, logging.INFO, automation='task_router', action='classify',
          classification=classification)

    result = {
        'timestamp': timestamp,
        'task': task_text,
        'classification': classification,
        'status': 'unknown'
    }

    try:
        if classification == 'github':
            # Add to GitHub TODO.md
            from services import add_task as github_add_task

            api_start = time.time()
            github_result = github_add_task(task_text)
            duration_ms = int((time.time() - api_start) * 1000)

            result['status'] = 'added_to_github'
            result['commit'] = github_result.get('commit')
            kvlog(logger, logging.NOTICE, automation='task_router', action='add_task',
                  destination='github', result='ok', duration_ms=duration_ms)

        elif classification == 'work':
            # Add to Checkvist work list
            from services.checkvist import add_task as checkvist_add_task

            api_start = time.time()
            checkvist_result = checkvist_add_task('work', task_text)
            duration_ms = int((time.time() - api_start) * 1000)

            result['status'] = 'added_to_checkvist_work'
            result['task_id'] = checkvist_result.get('task_id')
            kvlog(logger, logging.NOTICE, automation='task_router', action='add_task',
                  destination='checkvist_work', result='ok', duration_ms=duration_ms)

        elif classification == 'personal':
            # Add to Checkvist personal list
            from services.checkvist import add_task as checkvist_add_task

            api_start = time.time()
            checkvist_result = checkvist_add_task('personal', task_text)
            duration_ms = int((time.time() - api_start) * 1000)

            result['status'] = 'added_to_checkvist_personal'
            result['task_id'] = checkvist_result.get('task_id')
            kvlog(logger, logging.NOTICE, automation='task_router', action='add_task',
                  destination='checkvist_personal', result='ok', duration_ms=duration_ms)

        else:
            # Fallback - return instruction for Apple Reminders
            result['status'] = 'use_reminders'
            result['message'] = f"Please add to Reminders: {task_text}"
            kvlog(logger, logging.INFO, automation='task_router', action='fallback',
                  destination='apple_reminders')

        # Send notification
        try:
            from lib.notifications import send_low

            if result['status'].startswith('added'):
                send_low(f"Task added: {task_text}", title="✓ Task Captured")
                kvlog(logger, logging.INFO, automation='task_router', action='notification',
                      result='sent')
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='task_router', action='notification',
                  error_type=type(e).__name__, error_msg=str(e))

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='task_router', action='route_task',
              error_type=type(e).__name__, error_msg=str(e))
        result['status'] = 'error'
        result['error'] = str(e)

    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='task_router', event='complete',
          duration_ms=total_duration_ms, status=result['status'])

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        kvlog(logger, logging.ERROR, automation='task_router', error_type='UsageError',
              error_msg='No task text provided')
        sys.exit(1)

    task_text = ' '.join(sys.argv[1:])
    result = run(task_text)
