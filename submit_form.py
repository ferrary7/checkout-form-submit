#!/usr/bin/env python3
"""
Google Form Auto-Submission Script
Submits a daily progress form to Google Forms with randomized work tasks.
Configuration is loaded from config.json for easy customization.
"""

import requests
import random
import json
import os
from datetime import datetime
import sys


def load_config():
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json file not found!")
        print("Please create a config.json file with your form configuration.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config.json: {e}")
        sys.exit(1)


def generate_work_done(config):
    """Generate randomized work done list with required and optional tasks."""
    work_config = config['work_tasks']
    required_tasks = work_config['required_tasks'][:]
    optional_tasks = []
    
    # Add optional tasks based on their probability
    for task_info in work_config['optional_tasks']:
        if random.random() < task_info['probability']:
            optional_tasks.append(task_info['task'])
    
    # Combine and randomize order
    all_tasks = required_tasks + optional_tasks
    random.shuffle(all_tasks)
    
    # Format as bullet points
    return "\n".join(f"- {task}" for task in all_tasks)


def submit_google_form(config):
    """Submit the Google Form with today's data."""
    
    # Get current date
    now = datetime.now()
    
    # Extract config sections
    form_config = config['form_config']
    user_data = config['user_data']
    field_mappings = form_config['field_mappings']
    hidden_params = form_config['hidden_params']
    
    # Generate productivity rating
    rating_range = user_data['productivity_rating_range']
    productivity_rating = random.randint(rating_range['min'], rating_range['max'])
    
    # Generate form data
    form_data = {
        field_mappings['name']: user_data['name'],
        field_mappings['work_done']: generate_work_done(config),
        field_mappings['difficulties']: user_data['difficulties_default'],
        field_mappings['agenda']: user_data['agenda_default'],
        field_mappings['date_year']: str(now.year),
        field_mappings['date_month']: str(now.month),
        field_mappings['date_day']: str(now.day),
        field_mappings['productivity_rating']: str(productivity_rating)
    }
    
    # Add hidden parameters
    form_data.update(hidden_params)
    
    # Form submission URL
    url = form_config['form_url']
    
    # Headers to mimic browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # Submit the form
        response = requests.post(url, data=form_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("SUCCESS: Form submitted successfully")
            return True
        else:
            print(f"ERROR: Form submission failed with status code: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error submitting form: {str(e)}")
        return False


if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Print current date and user info for logging
    now = datetime.now()
    user_data = config['user_data']
    
    print(f"Date: {now.strftime('%Y-%m-%d')}")
    print(f"Time: {now.strftime('%H:%M:%S UTC')}")
    print(f"Submitter: {user_data['name']}")
    
    work_done = generate_work_done(config)
    print(f"Work Done:\n{work_done}")
    
    rating_range = user_data['productivity_rating_range']
    productivity_rating = random.randint(rating_range['min'], rating_range['max'])
    print(f"Productivity Rating: {productivity_rating}/{rating_range['max']}")
    
    print(f"\nSubmitting form...")
    
    success = submit_google_form(config)
    sys.exit(0 if success else 1)