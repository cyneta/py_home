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
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_task_ai(task_text):
    """
    Classify task using Claude AI

    Args:
        task_text: Task description

    Returns:
        str: 'github', 'work', 'personal', or None if AI unavailable
    """
    try:
        import anthropic
        import os

        # Get API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set, falling back to keyword classification")
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

        # Validate response
        if classification in ['github', 'work', 'personal']:
            logger.info(f"AI classified as: {classification}")
            return classification
        else:
            logger.warning(f"AI returned invalid classification: {classification}")
            return None

    except Exception as e:
        logger.warning(f"AI classification failed: {e}")
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
    logger.info("Using keyword-based classification")
    return classify_task_keywords(task_text)


def run(task_text):
    """
    Route task to appropriate system

    Args:
        task_text: Task description

    Returns:
        dict: Routing result
    """
    timestamp = datetime.now().isoformat()
    logger.info(f"Task router triggered at {timestamp}")
    logger.info(f"Task: {task_text}")

    classification = classify_task(task_text)
    logger.info(f"Classification: {classification}")

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

            github_result = github_add_task(task_text)
            result['status'] = 'added_to_github'
            result['commit'] = github_result.get('commit')
            logger.info(f"✓ Added to GitHub: {task_text}")

        elif classification == 'work':
            # Add to Checkvist work list
            from services.checkvist import add_task as checkvist_add_task

            checkvist_result = checkvist_add_task('work', task_text)
            result['status'] = 'added_to_checkvist_work'
            result['task_id'] = checkvist_result.get('task_id')
            logger.info(f"✓ Added to Checkvist (work): {task_text}")

        elif classification == 'personal':
            # Add to Checkvist personal list
            from services.checkvist import add_task as checkvist_add_task

            checkvist_result = checkvist_add_task('personal', task_text)
            result['status'] = 'added_to_checkvist_personal'
            result['task_id'] = checkvist_result.get('task_id')
            logger.info(f"✓ Added to Checkvist (personal): {task_text}")

        else:
            # Fallback - return instruction for Apple Reminders
            result['status'] = 'use_reminders'
            result['message'] = f"Please add to Reminders: {task_text}"
            logger.info(f"→ Use Apple Reminders for: {task_text}")

        # Send notification
        try:
            from lib.notifications import send_low

            if result['status'].startswith('added'):
                send_low(f"Task added: {task_text}", title="✓ Task Captured")
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

    except Exception as e:
        logger.error(f"✗ Failed to route task: {e}")
        result['status'] = 'error'
        result['error'] = str(e)

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python task_router.py <task text>")
        print("Example: python task_router.py 'Fix bug in leaving_home.py'")
        sys.exit(1)

    task_text = ' '.join(sys.argv[1:])
    result = run(task_text)

    # Print result
    print(f"\nTask: {result['task']}")
    print(f"Classification: {result['classification']}")
    print(f"Status: {result['status']}")

    if 'error' in result:
        print(f"Error: {result['error']}")
