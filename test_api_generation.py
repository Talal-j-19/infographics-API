#!/usr/bin/env python3
"""
Comprehensive test script for the Headless Infographic Generator API
Tests generation functionality and analyzes response quality
"""

import requests
import base64
import time
import json
import os
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_api_health(self):
        """Test if the API is running and healthy"""
        self.log("Testing API health...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"✅ API is healthy: {health_data}")
                return True
            else:
                self.log(f"❌ API health check failed: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Cannot connect to API: {e}", "ERROR")
            return False
    
    def test_api_info(self):
        """Test API root endpoint for basic info"""
        self.log("Testing API info endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                info_data = response.json()
                self.log(f"✅ API info retrieved: {info_data.get('service', 'Unknown')}")
                self.log(f"   Version: {info_data.get('version', 'Unknown')}")
                return True
            else:
                self.log(f"❌ API info failed: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ API info request failed: {e}", "ERROR")
            return False
    
    def analyze_svg_content(self, svg_content, variant_id):
        """Analyze SVG content for quality metrics"""
        self.log(f"Analyzing SVG content for variant {variant_id}...")
        
        analysis = {
            "variant_id": variant_id,
            "file_size": len(svg_content.encode('utf-8')),
            "has_xml_declaration": svg_content.strip().startswith('<?xml'),
            "has_svg_namespace": 'xmlns="http://www.w3.org/2000/svg"' in svg_content,
            "text_elements": svg_content.count('<text'),
            "shape_elements": {
                "circles": svg_content.count('<circle'),
                "rectangles": svg_content.count('<rect'),
                "paths": svg_content.count('<path'),
                "lines": svg_content.count('<line'),
                "polygons": svg_content.count('<polygon'),
                "ellipses": svg_content.count('<ellipse')
            },
            "groups": svg_content.count('<g'),
            "styles": svg_content.count('style='),
            "colors": svg_content.count('fill=') + svg_content.count('stroke='),
            "valid_xml": False,
            "svg_dimensions": {"width": None, "height": None}
        }
        
        # Check if it's valid XML
        try:
            root = ET.fromstring(svg_content)
            analysis["valid_xml"] = True
            
            # Extract SVG dimensions
            if root.tag.endswith('svg'):
                analysis["svg_dimensions"]["width"] = root.get('width')
                analysis["svg_dimensions"]["height"] = root.get('height')
                
        except ET.ParseError as e:
            self.log(f"⚠️  SVG XML parsing failed for variant {variant_id}: {e}", "WARNING")
        
        # Calculate quality score
        total_shapes = sum(analysis["shape_elements"].values())
        quality_score = 0
        
        if analysis["file_size"] > 1000:
            quality_score += 20
        if analysis["file_size"] > 5000:
            quality_score += 20
        if analysis["text_elements"] > 3:
            quality_score += 20
        if total_shapes > 5:
            quality_score += 20
        if analysis["valid_xml"]:
            quality_score += 10
        if analysis["has_svg_namespace"]:
            quality_score += 10
        
        analysis["quality_score"] = quality_score
        analysis["total_shapes"] = total_shapes
        
        # Quality rating
        if quality_score >= 80:
            analysis["quality_rating"] = "EXCELLENT"
        elif quality_score >= 60:
            analysis["quality_rating"] = "GOOD"
        elif quality_score >= 40:
            analysis["quality_rating"] = "FAIR"
        else:
            analysis["quality_rating"] = "POOR"
        
        return analysis
    
    def save_svg_file(self, svg_content, variant_id, test_name):
        """Save SVG content to file"""
        filename = f"{test_name}_variant_{variant_id}.svg"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        self.log(f"💾 Saved SVG: {filepath}")
        return str(filepath)
    
    def test_generation(self, prompt, style_preference="creative and modern", test_name="test"):
        """Test infographic generation with detailed analysis"""
        self.log(f"🎨 Testing generation: '{prompt}'")
        self.log(f"   Style: {style_preference}")
        self.log(f"   Test name: {test_name}")
        
        test_result = {
            "test_name": test_name,
            "prompt": prompt,
            "style_preference": style_preference,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "request_time": 0,
            "generation_time": 0,
            "variants": [],
            "errors": []
        }
        
        try:
            # Prepare request
            payload = {
                "prompt": prompt,
                "style_preference": style_preference
            }
            
            self.log("📤 Sending generation request...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/generate-infographics",
                json=payload
            )
            
            test_result["request_time"] = time.time() - start_time
            self.log(f"⏱️  Request completed in {test_result['request_time']:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                test_result["success"] = result.get("success", False)
                test_result["generation_time"] = result.get("generation_time", 0)
                
                self.log(f"✅ Generation successful!")
                self.log(f"   API Message: {result.get('message', 'No message')}")
                self.log(f"   Generation time: {test_result['generation_time']:.2f} seconds")
                self.log(f"   Output directory: {result.get('output_directory', 'Unknown')}")
                self.log(f"   Variants returned: {len(result.get('variants', []))}")
                
                # Analyze each variant
                for variant in result.get("variants", []):
                    variant_analysis = {
                        "variant_id": variant.get("variant_id"),
                        "success": variant.get("success", False),
                        "file_size": variant.get("file_size", 0),
                        "message": variant.get("message", ""),
                        "svg_file_path": variant.get("svg_file_path", ""),
                        "content_analysis": None,
                        "saved_file": None
                    }
                    
                    if variant.get("success") and variant.get("svg_content_base64"):
                        try:
                            # Decode SVG content
                            svg_content = base64.b64decode(variant["svg_content_base64"]).decode('utf-8')
                            
                            # Analyze content
                            variant_analysis["content_analysis"] = self.analyze_svg_content(
                                svg_content, variant["variant_id"]
                            )
                            
                            # Save file
                            variant_analysis["saved_file"] = self.save_svg_file(
                                svg_content, variant["variant_id"], test_name
                            )
                            
                            # Log analysis results
                            analysis = variant_analysis["content_analysis"]
                            self.log(f"   📊 Variant {variant['variant_id']} Analysis:")
                            self.log(f"      Quality: {analysis['quality_rating']} ({analysis['quality_score']}/100)")
                            self.log(f"      File size: {analysis['file_size']} bytes")
                            self.log(f"      Text elements: {analysis['text_elements']}")
                            self.log(f"      Total shapes: {analysis['total_shapes']}")
                            self.log(f"      Valid XML: {analysis['valid_xml']}")
                            
                        except Exception as e:
                            error_msg = f"Failed to process variant {variant['variant_id']}: {e}"
                            self.log(f"❌ {error_msg}", "ERROR")
                            test_result["errors"].append(error_msg)
                    else:
                        error_msg = f"Variant {variant.get('variant_id')} failed: {variant.get('message', 'Unknown error')}"
                        self.log(f"❌ {error_msg}", "ERROR")
                        test_result["errors"].append(error_msg)
                    
                    test_result["variants"].append(variant_analysis)
                
            else:
                error_msg = f"API request failed: {response.status_code}"
                self.log(f"❌ {error_msg}", "ERROR")
                test_result["errors"].append(error_msg)
                
                try:
                    error_detail = response.json()
                    self.log(f"   Error details: {error_detail}")
                    test_result["errors"].append(str(error_detail))
                except:
                    self.log(f"   Error text: {response.text}")
                    test_result["errors"].append(response.text)
        

            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.log(f"❌ {error_msg}", "ERROR")
            test_result["errors"].append(error_msg)
        
        self.test_results.append(test_result)
        return test_result
    
    def save_test_report(self):
        """Save comprehensive test report"""
        report_file = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        self.log(f"📄 Test report saved: {report_file}")
        return str(report_file)
    
    def print_summary(self):
        """Print test summary"""
        self.log("=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test["success"])
        
        self.log(f"Total tests: {total_tests}")
        self.log(f"Successful tests: {successful_tests}")
        self.log(f"Failed tests: {total_tests - successful_tests}")
        
        if total_tests > 0:
            success_rate = (successful_tests / total_tests) * 100
            self.log(f"Success rate: {success_rate:.1f}%")
        
        # Analyze variants
        total_variants = 0
        successful_variants = 0
        quality_scores = []
        
        for test in self.test_results:
            for variant in test["variants"]:
                total_variants += 1
                if variant["success"]:
                    successful_variants += 1
                    if variant["content_analysis"]:
                        quality_scores.append(variant["content_analysis"]["quality_score"])
        
        if total_variants > 0:
            variant_success_rate = (successful_variants / total_variants) * 100
            self.log(f"Variant success rate: {variant_success_rate:.1f}% ({successful_variants}/{total_variants})")
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            self.log(f"Average quality score: {avg_quality:.1f}/100")
            self.log(f"Quality range: {min(quality_scores)}-{max(quality_scores)}")

def main():
    """Main test function"""
    print("🧪 HEADLESS INFOGRAPHIC API GENERATION TEST")
    print("=" * 60)
    
    tester = APITester()
    
    # Test 1: API Health
    if not tester.test_api_health():
        print("\n💥 API is not running. Please start the API first:")
        print("   python start_api.py")
        return
    
    # Test 2: API Info
    tester.test_api_info()
    
    print("\n" + "=" * 60)
    
    # Test 3: Generation tests with different prompts
    test_cases = [
        {
            "prompt": "solar energy vs wind energy",
            "style": "professional and informative",
            "name": "energy_comparison"
        },
        {
            "prompt": "steps to make coffee",
            "style": "creative and modern",
            "name": "coffee_steps"
        },
        {
            "prompt": "machine learning algorithms",
            "style": "technical and detailed",
            "name": "ml_algorithms"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 GENERATION TEST {i}/{len(test_cases)}")
        print("=" * 40)
        
        result = tester.test_generation(
            test_case["prompt"], 
            test_case["style"],
            test_case["name"]
        )
        
        if result["success"]:
            print(f"✅ Test {i} PASSED")
        else:
            print(f"❌ Test {i} FAILED")
        
        if i < len(test_cases):
            print("\n⏳ Waiting 15 seconds before next test...")
            time.sleep(15)
    
    # Generate final report
    tester.print_summary()
    report_file = tester.save_test_report()
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")
    print(f"📁 Output directory: {tester.output_dir}")
    print(f"📄 Detailed report: {report_file}")

if __name__ == "__main__":
    main()
