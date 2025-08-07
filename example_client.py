#!/usr/bin/env python3
"""
Example client for the Headless Infographic Generator API
"""

import requests
import base64
import time
import json
from pathlib import Path

def test_api_health():
    """Test if the API is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def generate_infographics(prompt, style_preference="creative and modern"):
    """Generate infographics using the API"""
    print(f"\n🎨 Generating infographics for: '{prompt}'")
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
            json=payload
        )
        
        request_time = time.time() - start_time
        print(f"⏱️  Request completed in {request_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Generation successful!")
            print(f"   Message: {result['message']}")
            print(f"   Generation time: {result['generation_time']:.2f} seconds")
            print(f"   Output directory: {result['output_directory']}")
            print(f"   Variants generated: {len(result['variants'])}")
            
            # Create local output directory
            output_dir = Path("client_output")
            output_dir.mkdir(exist_ok=True)
            
            # Save each variant
            for variant in result["variants"]:
                if variant["success"]:
                    # Decode and save SVG
                    svg_content = base64.b64decode(variant["svg_content_base64"]).decode('utf-8')
                    
                    filename = f"infographic_variant_{variant['variant_id']}.svg"
                    local_file = output_dir / filename
                    
                    with open(local_file, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    
                    print(f"   💾 Saved variant {variant['variant_id']}: {local_file}")
                    print(f"      File size: {variant['file_size']} bytes")
                    
                    # Quick quality check
                    text_count = svg_content.count('<text')
                    shape_count = sum(svg_content.count(f'<{shape}') for shape in ['circle', 'rect', 'path', 'line'])
                    
                    print(f"      Content: {text_count} text elements, {shape_count} shapes")
                    
                    if variant['file_size'] > 5000 and text_count > 5:
                        print("      🏆 HIGH QUALITY SVG!")
                    elif variant['file_size'] > 1000 and text_count > 0:
                        print("      👍 GOOD QUALITY SVG!")
                    else:
                        print("      ⚠️  Basic SVG")
                else:
                    print(f"   ❌ Variant {variant['variant_id']} failed: {variant['message']}")
            
            return True, result
            
        else:
            print(f"❌ Generation failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Error: {response.text}")
            return False, None
            

    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def main():
    """Main example function"""
    print("🚀 HEADLESS INFOGRAPHIC GENERATOR API CLIENT")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_api_health():
        print("\n💥 API is not running. Please start the API first:")
        print("   python start_api.py")
        return
    
    print("\n" + "=" * 60)
    
    # Test 2: Generate infographics with different prompts
    test_prompts = [
        {
            "prompt": "solar energy vs wind energy",
            "style": "professional and informative"
        },
        {
            "prompt": "steps to make coffee",
            "style": "creative and modern"
        },
        {
            "prompt": "machine learning algorithms comparison",
            "style": "technical and detailed"
        }
    ]
    
    for i, test_case in enumerate(test_prompts, 1):
        print(f"\n🧪 TEST {i}/{len(test_prompts)}")
        print("=" * 40)
        
        success, result = generate_infographics(
            test_case["prompt"], 
            test_case["style"]
        )
        
        if success:
            print(f"✅ Test {i} PASSED")
        else:
            print(f"❌ Test {i} FAILED")
        
        if i < len(test_prompts):
            print("\n⏳ Waiting 10 seconds before next test...")
            time.sleep(10)
    
    print("\n" + "=" * 60)
    print("🎉 Example client completed!")
    print("📁 Check the 'client_output' directory for generated SVG files")

if __name__ == "__main__":
    main()
