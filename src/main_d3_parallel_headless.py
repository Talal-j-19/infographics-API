#!/usr/bin/env python3
"""
Main D3 Parallel Headless - Generate 3 infographic variants using headless SVG extraction
"""

import os
import sys
import time
import hashlib
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent))


async def headless_svg_extract_async(html_file, output_svg):
    """Async wrapper for headless SVG extraction"""
    from playwright.async_api import async_playwright
    
    print(f"[Headless] Starting extraction for {Path(html_file).parent.name}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1200, "height": 800})
            
            # Navigate to HTML file
            file_url = f"file://{Path(html_file).absolute()}"
            await page.goto(file_url, wait_until='networkidle', timeout=30000)
            
            # Wait for D3.js and SVG rendering
            await page.wait_for_timeout(3000)
            
            # Check D3.js availability
            d3_available = await page.evaluate("typeof d3 !== 'undefined'")
            if not d3_available:
                await page.wait_for_timeout(5000)
                d3_available = await page.evaluate("typeof d3 !== 'undefined'")
            
            if not d3_available:
                print(f"[Headless] ERROR: D3.js failed to load for {Path(html_file).parent.name}")
                return False
            
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
                print(f"[Headless] ERROR: Invalid SVG content for {Path(html_file).parent.name}")
                return False
            
            print(f"[Headless] SVG validated: {svg_info['children']} children, {svg_info['textElements']} text elements")
            
            # Extract SVG content
            svg_content = await page.evaluate("""
                () => {
                    const svg = document.querySelector('svg');
                    if (!svg) return null;
                    return svg.outerHTML;
                }
            """)
            
            if not svg_content:
                print(f"[Headless] ERROR: Failed to extract SVG for {Path(html_file).parent.name}")
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
            print(f"[Headless] SUCCESS: {Path(html_file).parent.name} → {output_svg} ({file_size} bytes)")
            
            return True
            
        except Exception as e:
            print(f"[Headless] ERROR for {Path(html_file).parent.name}: {e}")
            return False
            
        finally:
            await browser.close()


def headless_svg_extract_sync(html_file, output_svg):
    """Synchronous wrapper for headless extraction"""
    return asyncio.run(headless_svg_extract_async(html_file, output_svg))


def generate_single_variant_headless(topic, variant_id, base_output_dir):
    """Generate a single variant with headless SVG extraction"""

    print(f"\n🚀 [Variant {variant_id+1}] Starting generation...")

    try:
        # Import here to avoid circular imports
        from gemini_api_d3_single_frame import get_d3_code_single_frame
        from gemini_api_d3_headless import get_d3_code_headless_variant
        import json

        # Create variant directory
        variant_dir = base_output_dir / f"variant_{variant_id+1}"
        variant_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate HTML infographic using the same process as main_d3_parallel
        print(f"📝 [Variant {variant_id+1}] Generating D3.js infographic...")

        # Get elements for this variant
        elements_prompt = {
            "topic": topic,
            "task": f"List the key visual/text elements needed to make a single-frame D3.js infographic for this topic. Create a unique and creative approach - make this infographic different from typical ones. Variant {variant_id+1} of 3 - be creative and original. Return as a JSON list of element descriptions. Do not include code or explanations."
        }
        elements_response = get_d3_code_single_frame(elements_prompt)

        if not elements_response:
            print(f"❌ [Variant {variant_id+1}] Failed to get elements")
            return None

        # Get D3.js code for this variant using headless-optimized API
        code_prompt = {
            "topic": topic,
            "elements": elements_response,
            "variant_id": variant_id,
            "task": f"Generate complete D3.js infographic code for variant {variant_id+1}. Make it visually distinct and creative. Return complete HTML with proper structure for headless browser extraction."
        }
        d3_code = get_d3_code_headless_variant(code_prompt, variant_id)

        if not d3_code:
            print(f"❌ [Variant {variant_id+1}] Failed to generate D3.js code")
            return None

        # Save HTML file (no need for responsive scaling as it's built into headless API)
        html_file = variant_dir / "infographic.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(d3_code)

        print(f"✅ [Variant {variant_id+1}] HTML generated: {html_file}")
        
        # Step 2: Extract SVG using headless method
        print(f"🎨 [Variant {variant_id+1}] Extracting SVG with headless browser...")
        
        svg_file = variant_dir / "infographic.svg"
        
        # Add staggered delay to prevent browser conflicts
        delay_seconds = variant_id * 5  # 0, 5, 10 seconds delay
        if delay_seconds > 0:
            print(f"⏳ [Variant {variant_id+1}] Waiting {delay_seconds}s to prevent conflicts...")
            time.sleep(delay_seconds)
        
        svg_success = headless_svg_extract_sync(str(html_file), str(svg_file))
        
        if not svg_success:
            print(f"❌ [Variant {variant_id+1}] Failed to extract SVG")
            return None
        
        print(f"✅ [Variant {variant_id+1}] SVG extracted: {svg_file}")
        
        # Return file paths
        return {
            'variant_id': variant_id + 1,
            'html': str(html_file),
            'svg': str(svg_file),
            'directory': str(variant_dir)
        }
        
    except Exception as e:
        print(f"❌ [Variant {variant_id+1}] Error: {e}")
        return None


def main_d3_parallel_headless(topic):
    """Main function for parallel D3.js infographic generation with headless SVG extraction"""
    
    print("🚀 D3.js PARALLEL INFOGRAPHIC GENERATOR (HEADLESS)")
    print("="*60)
    print(f"Topic: {topic}")
    print("Method: Headless browser SVG extraction")
    print("Variants: 3 different visual styles")
    print()
    
    # Create output directory
    timestamp = int(time.time())
    topic_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_topic = "_".join(safe_topic.split())[:50]
    
    batch_name = f"batch_{timestamp}_{topic_hash}_{safe_topic}"
    output_dir = Path("generated") / batch_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Check Playwright availability
    try:
        import playwright
        print("✅ Playwright available")
    except ImportError:
        print("❌ Playwright not installed. Installing...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'playwright'], check=True)
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        print("✅ Playwright installed")
    
    # Generate variants in parallel (HTML generation)
    print("🔄 Generating HTML variants in parallel...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all variant generation tasks
        future_to_variant = {
            executor.submit(generate_single_variant_headless, topic, i, output_dir): i 
            for i in range(3)
        }
        
        results = []
        
        # Collect results as they complete
        for future in as_completed(future_to_variant):
            variant_id = future_to_variant[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"🎉 [Variant {variant_id+1}] COMPLETED")
                else:
                    print(f"💥 [Variant {variant_id+1}] FAILED")
            except Exception as e:
                print(f"💥 [Variant {variant_id+1}] EXCEPTION: {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    if results:
        print(f"✅ Successfully generated {len(results)}/3 variants")
        print()
        
        for result in sorted(results, key=lambda x: x['variant_id']):
            print(f"🎨 Variant {result['variant_id']}:")
            print(f"   📄 HTML: {result['html']}")
            print(f"   🖼️  SVG:  {result['svg']}")
            print(f"   📁 Dir:  {result['directory']}")
            
            # Check file sizes
            try:
                html_size = Path(result['html']).stat().st_size
                svg_size = Path(result['svg']).stat().st_size
                print(f"   📊 Sizes: HTML {html_size} bytes, SVG {svg_size} bytes")
            except:
                pass
            print()
        
        print(f"🎯 All files saved in: {output_dir}")
        print("🎉 PARALLEL HEADLESS GENERATION COMPLETE!")
        
        return True, str(output_dir), results
    else:
        print("❌ No variants were successfully generated")
        print("💡 Check the error messages above for troubleshooting")
        
        return False, str(output_dir), []


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main_d3_parallel_headless.py \"<topic>\"")
        print("Example: python main_d3_parallel_headless.py \"machine learning vs deep learning\"")
        sys.exit(1)
    
    topic = sys.argv[1]
    
    success, output_dir, results = main_d3_parallel_headless(topic)
    
    if success:
        print(f"\n🎉 SUCCESS! Generated {len(results)} variants")
        print(f"📁 Output: {output_dir}")
        sys.exit(0)
    else:
        print(f"\n💥 FAILURE! Check error messages above")
        sys.exit(1)
