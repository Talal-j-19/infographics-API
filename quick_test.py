#!/usr/bin/env python3
"""
Quick test script for rapid API testing during development
"""

import requests
import base64
import time
import json
from pathlib import Path

def quick_test(prompt="solar energy vs wind energy", save_files=True):
    """Quick test of the API with minimal output"""
    
    print(f"🚀 Quick test: '{prompt}'")
    
    # Health check
    try:
        health = requests.get("http://localhost:8000/health")
        if health.status_code != 200:
            print("❌ API not healthy")
            return False
    except:
        print("❌ API not running")
        return False
    
    print("✅ API is running")
    
    # Generate infographics
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/generate-infographics",
            json={
                "prompt": prompt,
                "style_preference": "creative and modern"
            }
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Success in {request_time:.1f}s (API: {result['generation_time']:.1f}s)")
            print(f"   Generated: {len(result['variants'])} variants")
            
            success_count = 0
            total_size = 0
            
            if save_files:
                output_dir = Path("quick_test_output")
                output_dir.mkdir(exist_ok=True)
            
            for variant in result["variants"]:
                if variant["success"]:
                    success_count += 1
                    size = variant["file_size"]
                    total_size += size
                    
                    print(f"   Variant {variant['variant_id']}: {size} bytes")
                    
                    if save_files and variant.get("svg_content_base64"):
                        # Save SVG file
                        svg_content = base64.b64decode(variant["svg_content_base64"]).decode('utf-8')
                        filename = output_dir / f"quick_test_variant_{variant['variant_id']}.svg"
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(svg_content)
                        
                        # Quick quality check
                        text_count = svg_content.count('<text')
                        shape_count = sum(svg_content.count(f'<{shape}') for shape in ['circle', 'rect', 'path', 'line'])
                        
                        quality = "🏆" if size > 5000 and text_count > 5 else "👍" if size > 1000 else "⚠️"
                        print(f"      {quality} {text_count} texts, {shape_count} shapes → {filename.name}")
                else:
                    print(f"   Variant {variant['variant_id']}: ❌ Failed - {variant.get('message', 'Unknown error')}")
            
            print(f"   Total: {success_count}/{len(result['variants'])} successful, {total_size} bytes")
            
            if save_files and success_count > 0:
                print(f"   📁 Files saved in: quick_test_output/")
            
            return success_count > 0
            
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error = response.json()
                print(f"   {error.get('detail', 'Unknown error')}")
            except:
                print(f"   {response.text}")
            return False
            

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function with multiple quick tests"""
    print("⚡ QUICK API TEST")
    print("=" * 30)
    
    # Test cases for quick validation
    test_prompts = [
        "coffee brewing process",
        "renewable energy types",
        "data science workflow"
    ]
    
    success_count = 0
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🧪 Test {i}/{len(test_prompts)}")
        
        if quick_test(prompt, save_files=(i == 1)):  # Only save files for first test
            success_count += 1
            print("✅ PASSED")
        else:
            print("❌ FAILED")
        
        if i < len(test_prompts):
            print("⏳ Waiting 10s...")
            time.sleep(10)
    
    print(f"\n📊 Results: {success_count}/{len(test_prompts)} tests passed")
    
    if success_count == len(test_prompts):
        print("🎉 All tests passed! API is working correctly.")
    elif success_count > 0:
        print("⚠️  Some tests failed. Check the errors above.")
    else:
        print("💥 All tests failed. Check API configuration.")

if __name__ == "__main__":
    main()
