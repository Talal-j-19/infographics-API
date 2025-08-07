#!/usr/bin/env python3
"""
Standalone SVG extractor script for headless browser extraction
This runs as a separate process to avoid Windows subprocess issues in FastAPI
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def extract_svg(html_file: str, output_svg: str, variant_name: str):
    """Extract SVG from HTML file using headless browser"""
    
    print(f"[EXTRACTOR] Starting extraction for {variant_name}")
    print(f"[EXTRACTOR] HTML file: {html_file}")
    print(f"[EXTRACTOR] Output SVG: {output_svg}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1200, "height": 800})
                
                # Navigate to HTML file
                file_url = f"file://{Path(html_file).absolute()}"
                print(f"[EXTRACTOR] Loading: {file_url}")
                await page.goto(file_url, wait_until='networkidle', timeout=30000)
                
                # Wait for D3.js and SVG rendering
                await page.wait_for_timeout(3000)
                
                # Check D3.js availability
                d3_available = await page.evaluate("typeof d3 !== 'undefined'")
                if not d3_available:
                    await page.wait_for_timeout(5000)
                    d3_available = await page.evaluate("typeof d3 !== 'undefined'")
                
                if not d3_available:
                    print(f"[EXTRACTOR] ERROR: D3.js failed to load for {variant_name}")
                    return False, "D3.js failed to load"
                
                print(f"[EXTRACTOR] D3.js loaded successfully for {variant_name}")
                
                # Wait for SVG
                await page.wait_for_selector('svg', timeout=15000)
                await page.wait_for_timeout(2000)
                
                # Validate SVG content
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
                
                if not svg_info or svg_info['children'] < 5:
                    print(f"[EXTRACTOR] ERROR: Invalid SVG content for {variant_name}")
                    return False, "Invalid SVG content"
                
                print(f"[EXTRACTOR] SVG validated for {variant_name}: {svg_info['children']} children, {svg_info['textElements']} text elements")
                
                # Extract SVG content as proper standalone SVG
                svg_content = await page.evaluate("""
                    () => {
                        const svg = document.querySelector('svg');
                        if (!svg) return null;

                        // Clone the SVG to avoid modifying the original
                        const svgClone = svg.cloneNode(true);

                        // Ensure proper SVG attributes
                        svgClone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

                        // Remove any existing style elements (we want clean inline styles)
                        const styleElements = svgClone.querySelectorAll('style');
                        styleElements.forEach(style => style.remove());

                        return svgClone.outerHTML;
                    }
                """)
                
                if not svg_content:
                    print(f"[EXTRACTOR] ERROR: Failed to extract SVG for {variant_name}")
                    return False, "Failed to extract SVG"
                
                # Save SVG file with proper XML declaration
                xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
                with open(output_svg, 'w', encoding='utf-8') as f:
                    f.write(xml_declaration + svg_content)
                
                file_size = len(svg_content.encode('utf-8'))
                print(f"[EXTRACTOR] SVG extracted successfully for {variant_name}: {file_size} bytes")
                
                return True, f"Success: {file_size} bytes"
                
            except Exception as e:
                error_msg = f"Extraction failed for {variant_name}: {str(e)}"
                print(f"[EXTRACTOR] ERROR: {error_msg}")
                return False, error_msg
                
            finally:
                await browser.close()
                
    except Exception as e:
        error_msg = f"Browser launch failed for {variant_name}: {str(e)}"
        print(f"[EXTRACTOR] ERROR: {error_msg}")
        return False, error_msg

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 4:
        print("Usage: python svg_extractor.py <html_file> <output_svg> <variant_name>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    output_svg = sys.argv[2]
    variant_name = sys.argv[3]
    
    # Run the extraction
    success, message = asyncio.run(extract_svg(html_file, output_svg, variant_name))
    
    if success:
        print(f"[EXTRACTOR] SUCCESS: {message}")
        sys.exit(0)
    else:
        print(f"[EXTRACTOR] FAILED: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
