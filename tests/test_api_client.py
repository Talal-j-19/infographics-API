#!/usr/bin/env python3
"""
Test API Client - Test the FastAPI headless infographic generator
"""

import requests
import json
import base64
import time
from pathlib import Path


def test_api_health():
    """Test the health endpoint"""
    print("🔍 Testing API health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False


def test_generate_infographics(prompt, style_preference="creative and modern"):
    """Test the infographic generation endpoint"""
    print(f"🎨 Testing infographic generation...")
    print(f"   Prompt: {prompt}")
    print(f"   Style: {style_preference}")
    
    try:
        # Prepare request
        payload = {
            "prompt": prompt,
            "style_preference": style_preference
        }
        
        print("📤 Sending request to API...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/generate-infographics",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        request_time = time.time() - start_time
        print(f"⏱️  Request completed in {request_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generation successful!")
            print(f"   Message: {result['message']}")
            print(f"   Generation time: {result['generation_time']:.2f} seconds")
            print(f"   Output directory: {result['output_directory']}")
            print(f"   Variants generated: {len(result['variants'])}")
            
            # Process variants
            for i, variant in enumerate(result['variants']):
                print(f"\n📊 Variant {variant['variant_id']}:")
                print(f"   Success: {variant['success']}")
                print(f"   File size: {variant['file_size']} bytes")
                print(f"   Message: {variant['message']}")
                
                if variant['success'] and variant['svg_content_base64']:
                    # Save SVG file locally for testing
                    svg_content = base64.b64decode(variant['svg_content_base64']).decode('utf-8')
                    local_file = f"test_api_variant_{variant['variant_id']}.svg"
                    
                    with open(local_file, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    
                    print(f"   💾 Saved locally: {local_file}")
                    
                    # Quick quality check
                    text_count = svg_content.count('<text')
                    shape_count = sum(svg_content.count(f'<{shape}') for shape in ['circle', 'rect', 'path', 'line'])
                    
                    print(f"   🎨 Content: {text_count} text elements, {shape_count} shapes")
                    
                    if variant['file_size'] > 5000 and text_count > 5:
                        print("   🏆 HIGH QUALITY SVG!")
                    elif variant['file_size'] > 1000 and text_count > 0:
                        print("   👍 GOOD QUALITY SVG!")
                    else:
                        print("   ⚠️  Basic SVG")
            
            return True, result
            
        else:
            print(f"❌ Generation failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Error: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (5 minutes)")
        return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, None


def main():
    """Main test function"""
    print("🚀 FASTAPI HEADLESS INFOGRAPHIC GENERATOR TEST")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_api_health():
        print("\n💥 API is not running. Please start the API first:")
        print("   python api_headless_infographic.py")
        return
    
    print("\n" + "=" * 60)
    
    # Test 2: Generate infographics
    test_prompts = [
        "solar energy vs wind energy",
        "steps to make coffee",
        "machine learning algorithms"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🧪 TEST {i}/{len(test_prompts)}")
        print("=" * 40)
        
        success, result = test_generate_infographics(prompt)
        
        if success:
            print(f"✅ Test {i} PASSED")
        else:
            print(f"❌ Test {i} FAILED")
        
        if i < len(test_prompts):
            print("\n⏳ Waiting 10 seconds before next test...")
            time.sleep(10)
    
    print("\n" + "=" * 60)
    print("🎉 API TESTING COMPLETE!")
    print("\n📖 For interactive testing, visit: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
