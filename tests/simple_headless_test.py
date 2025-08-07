#!/usr/bin/env python3
"""
Simple Headless Test - Direct Playwright test without complex script generation
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright


async def simple_headless_extract(html_file, output_svg):
    """Simple headless SVG extraction"""
    
    print(f"[Simple] Starting headless extraction")
    print(f"[Simple] Input: {html_file}")
    print(f"[Simple] Output: {output_svg}")
    
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=True)
        
        try:
            # Create new page
            page = await browser.new_page()
            
            # Set viewport
            await page.set_viewport_size({"width": 1200, "height": 800})
            
            # Navigate to HTML file
            file_url = f"file://{Path(html_file).absolute()}"
            print(f"[Simple] Loading: {file_url}")
            
            await page.goto(file_url, wait_until='networkidle', timeout=30000)
            
            # Wait for D3.js to load
            print("[Simple] Waiting for D3.js...")
            await page.wait_for_timeout(3000)
            
            # Check if D3.js is available
            d3_available = await page.evaluate("typeof d3 !== 'undefined'")
            print(f"[Simple] D3.js available: {d3_available}")
            
            if not d3_available:
                print("[Simple] D3.js not loaded, waiting longer...")
                await page.wait_for_timeout(5000)
                d3_available = await page.evaluate("typeof d3 !== 'undefined'")
            
            if not d3_available:
                print("[Simple] ERROR: D3.js failed to load")
                return False
            
            # Wait for SVG to be created
            print("[Simple] Waiting for SVG...")
            await page.wait_for_selector('svg', timeout=15000)
            await page.wait_for_timeout(2000)
            
            # Get SVG element count
            svg_info = await page.evaluate("""
                () => {
                    const svg = document.querySelector('svg');
                    if (!svg) return null;
                    return {
                        children: svg.children.length,
                        textElements: svg.querySelectorAll('text').length,
                        width: svg.getBoundingClientRect().width,
                        height: svg.getBoundingClientRect().height
                    };
                }
            """)
            
            if not svg_info:
                print("[Simple] No SVG found")
                return False
            
            print(f"[Simple] SVG info: {svg_info}")
            
            # Extract SVG content with simple approach
            svg_content = await page.evaluate("""
                () => {
                    const svg = document.querySelector('svg');
                    if (!svg) return null;
                    return svg.outerHTML;
                }
            """)
            
            if not svg_content:
                print("[Simple] Failed to extract SVG content")
                return False
            
            # Add XML declaration and namespace
            if not svg_content.startswith('<?xml'):
                svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_content
            
            if 'xmlns="http://www.w3.org/2000/svg"' not in svg_content:
                svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
            
            # Save SVG file
            with open(output_svg, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            file_size = Path(output_svg).stat().st_size
            print(f"[Simple] SVG saved: {output_svg} ({file_size} bytes)")
            
            return True
            
        except Exception as e:
            print(f"[Simple] Error: {e}")
            return False
            
        finally:
            await browser.close()


def simple_headless_test(html_file, output_svg="test_simple_headless.svg"):
    """Test simple headless approach"""
    
    print("🚀 SIMPLE HEADLESS TEST")
    print("="*40)
    
    try:
        success = asyncio.run(simple_headless_extract(html_file, output_svg))
        
        if success:
            print("\n✅ SIMPLE HEADLESS SUCCESS!")
            
            # Check quality
            if Path(output_svg).exists():
                file_size = Path(output_svg).stat().st_size
                print(f"📁 File: {output_svg} ({file_size} bytes)")
                
                with open(output_svg, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                text_count = content.count('<text')
                shape_count = sum(content.count(f'<{shape}') for shape in ['circle', 'rect', 'path', 'line'])
                
                print(f"🎨 Content: {text_count} text elements, {shape_count} shapes")
                
                if file_size > 5000 and text_count > 5:
                    print("🏆 HIGH QUALITY SVG!")
                elif file_size > 1000 and text_count > 0:
                    print("👍 GOOD QUALITY SVG!")
                else:
                    print("⚠️  Basic SVG")
            
            return True
        else:
            print("\n❌ SIMPLE HEADLESS FAILED!")
            return False
            
    except Exception as e:
        print(f"\n❌ SIMPLE HEADLESS ERROR: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_headless_test.py <html_file> [output_svg]")
        sys.exit(1)
    
    html_file = sys.argv[1]
    output_svg = sys.argv[2] if len(sys.argv) > 2 else "test_simple_headless.svg"
    
    if not Path(html_file).exists():
        print(f"Error: HTML file not found: {html_file}")
        sys.exit(1)
    
    success = simple_headless_test(html_file, output_svg)
    
    if success:
        print(f"\n🎉 SUCCESS!")
        sys.exit(0)
    else:
        print(f"\n💥 FAILURE!")
        sys.exit(1)
