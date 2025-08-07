#!/usr/bin/env python3
"""
Detailed response analysis script for API testing
Analyzes API responses and SVG content quality
"""

import requests
import base64
import json
import re
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

class ResponseAnalyzer:
    def __init__(self):
        self.analysis_results = []
    
    def analyze_api_response(self, response_data):
        """Analyze the complete API response structure"""
        print("🔍 ANALYZING API RESPONSE")
        print("=" * 40)
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "response_structure": {},
            "variants_analysis": [],
            "overall_quality": {}
        }
        
        # Analyze response structure
        print("📋 Response Structure:")
        required_fields = ["success", "message", "variants", "generation_time", "output_directory"]
        
        for field in required_fields:
            present = field in response_data
            analysis["response_structure"][field] = present
            status = "✅" if present else "❌"
            print(f"   {status} {field}: {present}")
        
        # Basic response info
        print(f"\n📊 Response Summary:")
        print(f"   Success: {response_data.get('success', 'Unknown')}")
        print(f"   Message: {response_data.get('message', 'No message')}")
        print(f"   Generation time: {response_data.get('generation_time', 0):.2f}s")
        print(f"   Output directory: {response_data.get('output_directory', 'Unknown')}")
        print(f"   Variants count: {len(response_data.get('variants', []))}")
        
        # Analyze each variant
        variants = response_data.get('variants', [])
        successful_variants = 0
        total_file_size = 0
        quality_scores = []
        
        for variant in variants:
            variant_analysis = self.analyze_variant(variant)
            analysis["variants_analysis"].append(variant_analysis)
            
            if variant_analysis["success"]:
                successful_variants += 1
                total_file_size += variant_analysis["file_size"]
                if variant_analysis["svg_analysis"]:
                    quality_scores.append(variant_analysis["svg_analysis"]["quality_score"])
        
        # Overall quality metrics
        analysis["overall_quality"] = {
            "total_variants": len(variants),
            "successful_variants": successful_variants,
            "success_rate": (successful_variants / len(variants) * 100) if variants else 0,
            "total_file_size": total_file_size,
            "average_file_size": total_file_size / successful_variants if successful_variants > 0 else 0,
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "quality_range": [min(quality_scores), max(quality_scores)] if quality_scores else [0, 0]
        }
        
        print(f"\n🎯 Overall Quality:")
        print(f"   Success rate: {analysis['overall_quality']['success_rate']:.1f}%")
        print(f"   Average file size: {analysis['overall_quality']['average_file_size']:.0f} bytes")
        print(f"   Average quality: {analysis['overall_quality']['average_quality_score']:.1f}/100")
        
        self.analysis_results.append(analysis)
        return analysis
    
    def analyze_variant(self, variant_data):
        """Analyze individual variant data"""
        print(f"\n🎨 Variant {variant_data.get('variant_id', 'Unknown')} Analysis:")
        
        analysis = {
            "variant_id": variant_data.get("variant_id"),
            "success": variant_data.get("success", False),
            "file_size": variant_data.get("file_size", 0),
            "message": variant_data.get("message", ""),
            "has_svg_content": bool(variant_data.get("svg_content_base64")),
            "svg_analysis": None
        }
        
        print(f"   Success: {analysis['success']}")
        print(f"   File size: {analysis['file_size']} bytes")
        print(f"   Message: {analysis['message']}")
        print(f"   Has SVG content: {analysis['has_svg_content']}")
        
        # Analyze SVG content if available
        if analysis["success"] and analysis["has_svg_content"]:
            try:
                svg_content = base64.b64decode(variant_data["svg_content_base64"]).decode('utf-8')
                analysis["svg_analysis"] = self.analyze_svg_content(svg_content)
                
                svg_analysis = analysis["svg_analysis"]
                print(f"   📊 SVG Quality: {svg_analysis['quality_rating']} ({svg_analysis['quality_score']}/100)")
                print(f"   📝 Text elements: {svg_analysis['text_elements']}")
                print(f"   🎨 Shape elements: {svg_analysis['total_shapes']}")
                print(f"   ✅ Valid XML: {svg_analysis['valid_xml']}")
                print(f"   📐 Dimensions: {svg_analysis['svg_dimensions']['width']}x{svg_analysis['svg_dimensions']['height']}")
                
            except Exception as e:
                print(f"   ❌ SVG analysis failed: {e}")
        
        return analysis
    
    def analyze_svg_content(self, svg_content):
        """Detailed SVG content analysis"""
        analysis = {
            "file_size": len(svg_content.encode('utf-8')),
            "line_count": len(svg_content.split('\n')),
            "has_xml_declaration": svg_content.strip().startswith('<?xml'),
            "has_svg_namespace": 'xmlns="http://www.w3.org/2000/svg"' in svg_content,
            "has_d3_references": 'd3' in svg_content.lower(),
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
            "colors": {
                "fill_attributes": svg_content.count('fill='),
                "stroke_attributes": svg_content.count('stroke='),
                "color_values": len(re.findall(r'#[0-9a-fA-F]{6}', svg_content))
            },
            "transforms": svg_content.count('transform='),
            "animations": svg_content.count('<animate'),
            "valid_xml": False,
            "svg_dimensions": {"width": None, "height": None},
            "content_complexity": {}
        }
        
        # Check XML validity
        try:
            root = ET.fromstring(svg_content)
            analysis["valid_xml"] = True
            
            if root.tag.endswith('svg'):
                analysis["svg_dimensions"]["width"] = root.get('width')
                analysis["svg_dimensions"]["height"] = root.get('height')
                
        except ET.ParseError:
            pass
        
        # Calculate content complexity
        total_shapes = sum(analysis["shape_elements"].values())
        analysis["total_shapes"] = total_shapes
        
        analysis["content_complexity"] = {
            "element_density": (total_shapes + analysis["text_elements"]) / max(analysis["file_size"] / 1000, 1),
            "style_richness": analysis["styles"] + analysis["colors"]["fill_attributes"] + analysis["colors"]["stroke_attributes"],
            "structural_complexity": analysis["groups"] + analysis["transforms"],
            "color_variety": analysis["colors"]["color_values"]
        }
        
        # Calculate quality score
        quality_score = 0
        
        # File size scoring (0-25 points)
        if analysis["file_size"] > 10000:
            quality_score += 25
        elif analysis["file_size"] > 5000:
            quality_score += 20
        elif analysis["file_size"] > 2000:
            quality_score += 15
        elif analysis["file_size"] > 1000:
            quality_score += 10
        
        # Content scoring (0-25 points)
        if analysis["text_elements"] > 10:
            quality_score += 25
        elif analysis["text_elements"] > 5:
            quality_score += 20
        elif analysis["text_elements"] > 2:
            quality_score += 15
        elif analysis["text_elements"] > 0:
            quality_score += 10
        
        # Shape complexity (0-25 points)
        if total_shapes > 20:
            quality_score += 25
        elif total_shapes > 10:
            quality_score += 20
        elif total_shapes > 5:
            quality_score += 15
        elif total_shapes > 2:
            quality_score += 10
        
        # Technical quality (0-25 points)
        if analysis["valid_xml"]:
            quality_score += 10
        if analysis["has_svg_namespace"]:
            quality_score += 5
        if analysis["has_xml_declaration"]:
            quality_score += 5
        if analysis["colors"]["color_values"] > 3:
            quality_score += 5
        
        analysis["quality_score"] = quality_score
        
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
    
    def save_analysis_report(self, filename="response_analysis.json"):
        """Save detailed analysis report"""
        output_dir = Path("analysis_output")
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / filename
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Analysis report saved: {report_file}")
        return str(report_file)

def test_and_analyze(prompt="machine learning vs deep learning"):
    """Test API and analyze response"""
    print("🧪 API TEST AND RESPONSE ANALYSIS")
    print("=" * 50)
    
    analyzer = ResponseAnalyzer()
    
    # Test API
    try:
        print(f"🎯 Testing prompt: '{prompt}'")
        
        response = requests.post(
            "http://localhost:8000/generate-infographics",
            json={
                "prompt": prompt,
                "style_preference": "professional and detailed"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Analyze response
            analysis = analyzer.analyze_api_response(result)
            
            # Save analysis
            report_file = analyzer.save_analysis_report(
                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            print(f"\n🎉 Analysis completed successfully!")
            return True
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    test_and_analyze()
