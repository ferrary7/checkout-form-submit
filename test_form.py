#!/usr/bin/env python3
"""
Test script to verify form submission without submitting actual data.
This script will test the connection and form structure.
"""

import requests
import json
import os


def test_form_access():
    """Test if we can access the form and get its structure."""
    
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    form_url = config['form_config']['form_url']
    form_view_url = form_url.replace('/formResponse', '/viewform')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        print(f"Testing access to form: {form_view_url}")
        response = requests.get(form_view_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("SUCCESS: Can access form page")
            print(f"Form title found: {'form' in response.text.lower()}")
            
            # Check if our field mappings exist in the form
            field_mappings = config['form_config']['field_mappings']
            found_fields = []
            for field_name, field_id in field_mappings.items():
                if field_id in response.text:
                    found_fields.append(field_name)
            
            print(f"Found {len(found_fields)}/{len(field_mappings)} field mappings:")
            for field in found_fields:
                print(f"  ✓ {field}")
            
            missing_fields = set(field_mappings.keys()) - set(found_fields)
            if missing_fields:
                print("Missing fields:")
                for field in missing_fields:
                    print(f"  ✗ {field} ({field_mappings[field]})")
            
            return len(found_fields) == len(field_mappings)
        else:
            print(f"ERROR: Cannot access form (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    print("=== Google Form Access Test ===")
    success = test_form_access()
    
    if success:
        print("\n✓ Form access test PASSED")
        print("Your form configuration appears to be correct!")
    else:
        print("\n✗ Form access test FAILED")
        print("Check your form URL and field mappings in config.json")