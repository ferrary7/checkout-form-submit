#!/usr/bin/env python3
"""
Google Form Auto-Submission Script using Selenium
Submits a daily progress form using a real browser to avoid anti-bot measures.
Configuration is loaded from config.json for easy customization.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import json
import os
from datetime import datetime
import sys
import time


def load_config():
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json file not found!")
        print("Please create a config.json file with your form configuration.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config.json: {e}")
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


def setup_driver():
    """Set up Chrome WebDriver with appropriate options."""
    chrome_options = Options()
    
    # Headless mode for GitHub Actions
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Additional options to avoid detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"ERROR: Failed to setup Chrome driver: {e}")
        print("Make sure Chrome is installed and chromedriver is available in PATH")
        sys.exit(1)


def fill_form_selenium(driver, config):
    """Fill and submit the Google Form using Selenium."""
    
    # Extract config data
    user_data = config['user_data']
    rating_range = user_data['productivity_rating_range']
    productivity_rating = random.randint(rating_range['min'], rating_range['max'])
    work_done = generate_work_done(config)
    now = datetime.now()
    
    # Form URL (use viewform, not formResponse)
    form_url = config['form_config']['form_url'].replace('/formResponse', '/viewform')
    
    try:
        print("Loading form page...")
        driver.get(form_url)
        
        # Wait for form to load
        WebDriverWait(driver, 10).wait(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        time.sleep(2)
        
        # Find all input elements
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], textarea")
        
        print(f"Found {len(inputs)} input fields")
        
        # Fill fields based on common patterns
        filled_count = 0
        for i, input_elem in enumerate(inputs):
            try:
                # Get the parent element to find labels
                parent = input_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'freebirdFormviewerComponentsQuestionBaseRoot')]")
                question_text = parent.text.lower()
                
                # Fill based on question content
                if any(keyword in question_text for keyword in ['name', 'naam']):
                    input_elem.clear()
                    input_elem.send_keys(user_data['name'])
                    print(f"Filled name field: {user_data['name']}")
                    filled_count += 1
                    
                elif any(keyword in question_text for keyword in ['work done', 'work', 'progress', 'today']):
                    if input_elem.tag_name == 'textarea':
                        input_elem.clear()
                        input_elem.send_keys(work_done)
                        print(f"Filled work done field")
                        filled_count += 1
                    
                elif any(keyword in question_text for keyword in ['difficult', 'challenge', 'problem', 'issue']):
                    input_elem.clear()
                    input_elem.send_keys(user_data['difficulties_default'])
                    print(f"Filled difficulties field: {user_data['difficulties_default']}")
                    filled_count += 1
                    
                elif any(keyword in question_text for keyword in ['agenda', 'tomorrow', 'next', 'plan']):
                    input_elem.clear()
                    input_elem.send_keys(user_data['agenda_default'])
                    print(f"Filled agenda field: {user_data['agenda_default']}")
                    filled_count += 1
                    
            except Exception as e:
                # Skip this input if we can't process it
                continue
        
        # Handle date fields
        date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[aria-label*='year'], input[aria-label*='month'], input[aria-label*='day']")
        for date_input in date_inputs:
            try:
                aria_label = date_input.get_attribute('aria-label', '').lower()
                if 'year' in aria_label:
                    date_input.clear()
                    date_input.send_keys(str(now.year))
                elif 'month' in aria_label:
                    date_input.clear()
                    date_input.send_keys(str(now.month))
                elif 'day' in aria_label:
                    date_input.clear()
                    date_input.send_keys(str(now.day))
                elif date_input.get_attribute('type') == 'date':
                    date_input.clear()
                    date_input.send_keys(now.strftime('%Y-%m-%d'))
                filled_count += 1
            except:
                continue
        
        # Handle productivity rating (radio buttons or dropdowns)
        try:
            # Try to find radio buttons first
            rating_elements = driver.find_elements(By.CSS_SELECTOR, f"input[value='{productivity_rating}'], span[data-value='{productivity_rating}']")
            if rating_elements:
                rating_elements[0].click()
                print(f"Selected productivity rating: {productivity_rating}")
                filled_count += 1
            else:
                # Try to find by text content
                rating_xpath = f"//span[contains(text(), '{productivity_rating}')]"
                rating_elements = driver.find_elements(By.XPATH, rating_xpath)
                if rating_elements:
                    rating_elements[0].click()
                    print(f"Selected productivity rating: {productivity_rating}")
                    filled_count += 1
        except:
            pass
        
        print(f"Filled {filled_count} fields")
        
        # Submit the form
        submit_button = None
        submit_selectors = [
            "input[type='submit']",
            "button[type='submit']", 
            "div[role='button']",
            "[aria-label*='Submit']",
            "[data-submit='true']"
        ]
        
        for selector in submit_selectors:
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                if submit_button.is_displayed() and submit_button.is_enabled():
                    break
            except NoSuchElementException:
                continue
        
        if not submit_button:
            # Try finding submit button by text
            submit_texts = ['Submit', 'Send', 'Submit Form', 'Done']
            for text in submit_texts:
                try:
                    submit_button = driver.find_element(By.XPATH, f"//span[contains(text(), '{text}')]/parent::*")
                    if submit_button.is_displayed():
                        break
                except NoSuchElementException:
                    continue
        
        if submit_button:
            print("Submitting form...")
            driver.execute_script("arguments[0].scrollIntoView();", submit_button)
            time.sleep(1)
            submit_button.click()
            
            # Wait for submission to complete
            time.sleep(3)
            
            # Check if we're on a success/confirmation page
            current_url = driver.current_url
            page_text = driver.page_source.lower()
            
            if 'formresponse' in current_url or any(word in page_text for word in ['submitted', 'thank you', 'received', 'response recorded']):
                print("SUCCESS: Form submitted successfully")
                return True
            else:
                print("WARNING: Form may not have been submitted - no confirmation detected")
                return False
        else:
            print("ERROR: Could not find submit button")
            return False
            
    except TimeoutException:
        print("ERROR: Form took too long to load")
        return False
    except Exception as e:
        print(f"ERROR: Exception during form submission: {e}")
        return False


def submit_google_form_selenium(config):
    """Main function to submit Google Form using Selenium."""
    driver = None
    try:
        driver = setup_driver()
        return fill_form_selenium(driver, config)
    finally:
        if driver:
            driver.quit()


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
    
    print(f"\nSubmitting form using Selenium...")
    
    success = submit_google_form_selenium(config)
    sys.exit(0 if success else 1)