#!/usr/bin/env python3
"""
FastAPI Headless Infographic Generator - API endpoint for parallel infographic generation
"""

import sys
import time
import hashlib
import asyncio
import base64
import platform
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright

# Fix Windows event loop policy issue for subprocess
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent))


class InfographicRequest(BaseModel):
    prompt: str
    style_preference: str = "creative and modern"


class InfographicResponse(BaseModel):
    success: bool
    message: str
    variants: List[Dict[str, Any]]
    generation_time: float
    output_directory: str


app = FastAPI(
    title="Headless Infographic Generator API",
    description="Generate 3 different D3.js infographic variants using headless browser extraction",
    version="1.0.0"
)


async def headless_svg_extract_async(html_file: str, output_svg: str, variant_name: str):
    """Async headless SVG extraction - same as main file"""

    print(f"[API] Starting headless extraction for {variant_name}")

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
                print(f"[API] ERROR: D3.js failed to load for {variant_name}")
                return False, "D3.js failed to load"

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
                print(f"[API] ERROR: Invalid SVG content for {variant_name}")
                return False, "Invalid SVG content"

            print(f"[API] SVG validated for {variant_name}: {svg_info['children']} children, {svg_info['textElements']} text elements")

            # Extract SVG content
            svg_content = await page.evaluate("""
                () => {
                    const svg = document.querySelector('svg');
                    if (!svg) return null;
                    return svg.outerHTML;
                }
            """)
            
            if not svg_content:
                print(f"[API] ERROR: Failed to extract SVG for {variant_name}")
                return False, "Failed to extract SVG"
            
            # Add XML declaration and namespace
            if not svg_content.startswith('<?xml'):
                svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_content
            
            if 'xmlns="http://www.w3.org/2000/svg"' not in svg_content:
                svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
            
            # Save SVG file
            with open(output_svg, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            file_size = Path(output_svg).stat().st_size
            print(f"[API] SUCCESS: {variant_name} → {output_svg} ({file_size} bytes)")
            
            return True, f"Success: {file_size} bytes"
            
        except Exception as e:
            print(f"[API] ERROR for {variant_name}: {e}")
            return False, f"Error: {str(e)}"
            
        finally:
            await browser.close()


def generate_single_variant_api(topic: str, variant_id: int, base_output_dir: Path):
    """Generate a single variant for API"""
    
    print(f"[API] Starting variant {variant_id+1} generation...")
    
    try:
        # Import here to avoid circular imports
        from gemini_api_d3_single_frame import get_d3_code_single_frame
        from gemini_api_d3_headless import get_d3_code_headless_variant
        
        # Create variant directory
        variant_dir = base_output_dir / f"variant_{variant_id+1}"
        variant_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Get elements for this variant
        elements_prompt = {
            "topic": topic,
            "task": f"List the key visual/text elements needed to make a single-frame D3.js infographic for this topic. Create a unique and creative approach - make this infographic different from typical ones. Variant {variant_id+1} of 3 - be creative and original. Return as a JSON list of element descriptions. Do not include code or explanations."
        }
        elements_response = get_d3_code_single_frame(elements_prompt)

        if not elements_response:
            print(f"[API] Failed to get elements for variant {variant_id+1}")
            elements_response = "basic elements"
        else:
            print(f"[API] Elements for variant {variant_id+1}: {elements_response}")

        # Step 2: Generate D3.js code using headless-optimized API
        code_prompt = {
            "topic": topic,
            "elements": elements_response,
            "variant_id": variant_id,
            "task": f"Generate complete D3.js infographic code for variant {variant_id+1}. Make it visually distinct and creative. Return complete HTML with proper structure for headless browser extraction."
        }
        d3_code = get_d3_code_headless_variant(code_prompt, variant_id)

        if not d3_code:
            print(f"[API] Failed to generate D3.js code for variant {variant_id+1}")
            return None
        
        # Save HTML file
        html_file = variant_dir / "infographic.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(d3_code)
        
        print(f"[API] HTML generated for variant {variant_id+1}: {html_file}")
        
        return {
            'variant_id': variant_id + 1,
            'html': str(html_file),
            'directory': str(variant_dir),
            'status': 'html_generated'
        }
        
    except Exception as e:
        print(f"[API] Error generating variant {variant_id+1}: {e}")
        return None


def extract_svg_subprocess(html_file: str, output_svg: str, variant_name: str):
    """Extract SVG using separate subprocess to avoid Windows limitations"""

    print(f"[API] Starting subprocess extraction for {variant_name}")

    import subprocess
    import sys

    # Get the path to the svg_extractor.py script
    script_path = Path(__file__).parent / "svg_extractor.py"

    # Run the extractor as a separate process
    try:
        result = subprocess.run([
            sys.executable, str(script_path),
            html_file, output_svg, variant_name
        ], capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print(f"[API] Subprocess extraction successful for {variant_name}")
            # Parse the success message to get file size
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if "SUCCESS:" in line and "bytes" in line:
                    return True, line.split("SUCCESS: ")[1]
            return True, "Success"
        else:
            error_msg = f"Subprocess failed: {result.stderr}"
            print(f"[API] Subprocess extraction failed for {variant_name}: {error_msg}")
            return False, error_msg

    except subprocess.TimeoutExpired:
        error_msg = "Extraction timeout (120s)"
        print(f"[API] Subprocess timeout for {variant_name}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Subprocess error: {str(e)}"
        print(f"[API] Subprocess error for {variant_name}: {error_msg}")
        return False, error_msg

def extract_svgs_sequential(results: List[Dict], base_output_dir: Path):
    """Extract SVGs sequentially using thread pool to avoid Windows subprocess issues"""

    svg_results = []

    for i, result in enumerate(results):
        if not result:
            continue

        variant_id = result['variant_id']
        html_file = result['html']
        svg_file = Path(result['directory']) / "infographic.svg"

        # Add staggered delay
        delay_seconds = i * 3  # 0, 3, 6 seconds delay
        if delay_seconds > 0:
            print(f"[API] Waiting {delay_seconds}s before extracting variant {variant_id}...")
            time.sleep(delay_seconds)

        print(f"[API] Extracting SVG for variant {variant_id}...")

        # Use subprocess to avoid Windows asyncio limitations
        success, message = extract_svg_subprocess(
            html_file,
            str(svg_file),
            f"variant_{variant_id}"
        )
        
        if success:
            # Read SVG content and encode as base64
            with open(svg_file, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            file_size = Path(svg_file).stat().st_size
            
            svg_results.append({
                'variant_id': variant_id,
                'success': True,
                'svg_file': str(svg_file),
                'svg_content_base64': svg_base64,
                'file_size': file_size,
                'message': message
            })
        else:
            svg_results.append({
                'variant_id': variant_id,
                'success': False,
                'svg_file': str(svg_file),
                'svg_content_base64': None,
                'file_size': 0,
                'message': message
            })
    
    return svg_results


@app.post("/generate-infographics", response_model=InfographicResponse)
async def generate_infographics(request: InfographicRequest):
    """
    Generate 3 different infographic variants from a prompt
    
    Returns:
    - success: Whether the generation was successful
    - message: Status message
    - variants: List of generated variants with SVG content (base64 encoded)
    - generation_time: Total time taken
    - output_directory: Directory where files are saved
    """
    
    start_time = time.time()
    topic = request.prompt.strip()
    
    if not topic:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    print(f"[API] Starting infographic generation for: {topic}")
    
    try:
        # Create output directory
        timestamp = int(time.time())
        topic_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_topic = "_".join(safe_topic.split())[:50]
        
        batch_name = f"api_batch_{timestamp}_{topic_hash}_{safe_topic}"
        output_dir = Path("generated") / batch_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[API] Output directory: {output_dir}")
        
        # Step 1: Generate HTML variants in parallel
        print("[API] Generating HTML variants in parallel...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_variant = {
                executor.submit(generate_single_variant_api, topic, i, output_dir): i 
                for i in range(3)
            }
            
            html_results = []
            
            for future in as_completed(future_to_variant):
                variant_id = future_to_variant[future]
                try:
                    result = future.result()
                    if result:
                        html_results.append(result)
                        print(f"[API] HTML generation completed for variant {variant_id+1}")
                    else:
                        print(f"[API] HTML generation failed for variant {variant_id+1}")
                except Exception as e:
                    print(f"[API] Exception in variant {variant_id+1}: {e}")
        
        if not html_results:
            raise HTTPException(status_code=500, detail="Failed to generate any HTML variants")
        
        print(f"[API] Successfully generated {len(html_results)}/3 HTML variants")
        
        # Step 2: Extract SVGs sequentially
        print("[API] Extracting SVGs with headless browser...")
        
        svg_results = extract_svgs_sequential(html_results, output_dir)
        
        successful_svgs = [r for r in svg_results if r['success']]
        
        if not successful_svgs:
            raise HTTPException(status_code=500, detail="Failed to extract any SVGs")
        
        # Prepare response
        generation_time = time.time() - start_time
        
        response_variants = []
        for svg_result in svg_results:
            response_variants.append({
                'variant_id': svg_result['variant_id'],
                'success': svg_result['success'],
                'svg_content_base64': svg_result['svg_content_base64'],
                'file_size': svg_result['file_size'],
                'message': svg_result['message'],
                'svg_file_path': svg_result['svg_file']
            })
        
        print(f"[API] Generation completed in {generation_time:.2f} seconds")
        print(f"[API] Successfully generated {len(successful_svgs)}/3 SVG variants")
        
        return InfographicResponse(
            success=True,
            message=f"Successfully generated {len(successful_svgs)}/3 infographic variants",
            variants=response_variants,
            generation_time=generation_time,
            output_directory=str(output_dir)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[API] Unexpected error: {e}")
        print(f"[API] Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "headless-infographic-generator"}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Headless Infographic Generator API",
        "version": "1.0.0",
        "description": "Generate 3 different D3.js infographic variants using headless browser extraction",
        "endpoints": {
            "POST /generate-infographics": "Generate infographics from a prompt",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Headless Infographic Generator API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔗 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "api_headless_infographic:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
