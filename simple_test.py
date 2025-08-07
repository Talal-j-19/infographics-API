#!/usr/bin/env python3

import requests
import json

def test_simple_request():
    """Test with a simple request to check CSS embedding"""
    
    print("Testing simple coffee brewing infographic...")
    
    try:
        response = requests.post('http://localhost:8000/generate-infographics',
            json={'prompt': 'simple coffee brewing', 'num_variants': 1},
            timeout=180
        )
        
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Response keys: {list(result.keys())}')
            print(f'Full response: {result}')
        else:
            print(f'Error: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

if __name__ == "__main__":
    test_simple_request()
