def get_d3_code_headless_variant(prompt, variant_id=0, style_variant=None):
    """
    Generate D3.js code specifically optimized for headless browser extraction
    Returns properly formatted HTML that works reliably with Playwright
    """
    import os
    from dotenv import load_dotenv
    import google.generativeai as genai

    # Load .env file so environment variables are available
    load_dotenv()

    # Load API key from environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

    # If prompt is a dict and has a 'task', branch logic
    if isinstance(prompt, dict) and 'task' in prompt:
        task = prompt['task'].lower()
        if 'list' in task and 'element' in task:
            # Step 1: List elements for the infographic
            system_prompt = (
                "You are a D3.js infographic designer. "
                "Given a topic, return a JSON list of the key D3.js elements (e.g., SVG, rect, text, circle, line, group, axis, etc.) needed to make a single-frame D3.js infographic. "
                "Choose only valid D3.js and SVG elements. "
                "The elements should be chosen to make the infographic as informative as possible, but must not crowd the screen and must not overlap. "
                "Only include enough elements to fit one screen and be visually clear. "
                "Pay special attention to layout boundaries: No text or element should go outside the visible SVG area or overlap with other elements. "
                "All text and diagram elements must be placed so that they fit within the SVG canvas, with appropriate padding from the edges. "
                "Text labels, section titles, and formulas must not overlap with each other or with diagram elements. Adjust font size, wrapping, or positioning as needed to ensure clarity and no overflow. "
                "If there is not enough space, reduce the number of elements or use ellipsis, but never let text go outside the canvas or overlap. "
                "Return ONLY a JSON list of element descriptions, no code, no explanations, no markdown."
            )
            user_prompt = (
                f"Topic: {prompt.get('topic', '')}\n"
                f"{prompt.get('task', '')}"
            )
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=system_prompt
            )
            response = model.generate_content(user_prompt)
            elements = response.text.strip()
            # Remove accidental code blocks
            if elements.startswith("```json"):
                elements = elements[7:]
            if elements.startswith("```"):
                elements = elements[3:]
            if elements.endswith("```"):
                elements = elements[:-3]
            elements = elements.strip()
            return elements
        elif 'code' in task:
            # Step 2: Generate code optimized for headless extraction
            system_prompt = (
                "You are a D3.js expert who creates beautiful, informative, and highly readable single-frame infographics specifically optimized for headless browser extraction. "
                "CRITICAL REQUIREMENTS FOR HEADLESS COMPATIBILITY: "
                "1. You must return COMPLETE, VALID HTML with proper DOCTYPE, html, head, and body tags "
                "2. Use ONLY forward slashes (/) in closing tags - NEVER use backslashes (\\) "
                "3. Use ONLY standard HTML comments (/* */) - NEVER use backslash comments "
                "4. Include proper meta charset and viewport tags "
                "5. Load D3.js from CDN with proper script tags "
                "6. Create a container div with id for D3.js to target "
                "7. All JavaScript must be in proper script tags "
                "8. You must ONLY use valid D3.js (v7+) and SVG syntax and functions "
                "9. You must ONLY return valid HTML+JS code, with NO explanations, NO markdown, and NO ```html or ``` blocks "
                "10. The output must be a single static frame (no animation unless requested) "
                "11. All information about the topic must be visible in that single frame "
                "12. Text and labels must be well-placed, non-overlapping, and clearly readable "
                "13. Include key concepts and explanations with clear, non-crowded diagrams "
                "14. Do NOT use any custom or undefined classes, functions, or imports "
                "15. Do NOT try to explain in so much detail that the frame becomes crowded or unreadable "
                "16. Use ONLY the provided elements "
                "IMPORTANT SIZING CONSTRAINTS: Create SVG with dimensions that fit comfortably on standard screens. "
                "Recommended SVG size: width=800-1000px, height=600-800px maximum. Avoid creating very tall infographics (>900px height) that require excessive scrolling. "
                "Design for landscape orientation when possible. If content requires more height, use compact layouts, smaller fonts, or multi-column arrangements. "
                "Pay special attention to layout boundaries: No text or element should go outside the visible SVG area or overlap with other elements. "
                "All text and diagram elements must be placed so that they fit within the SVG canvas, with appropriate padding from the edges. "
                "Text labels, section titles, and formulas must not overlap with each other or with diagram elements. Adjust font size, wrapping, or positioning as needed to ensure clarity and no overflow. "
                "If there is not enough space, reduce the number of elements, use smaller fonts, or create a more compact layout, but never let text go outside the canvas or overlap. "
                "EXAMPLE STRUCTURE: "
                "<!DOCTYPE html> "
                "<html lang=\"en\"> "
                "<head> "
                "    <meta charset=\"UTF-8\"> "
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"> "
                "    <title>Infographic Title</title> "
                "    <script src=\"https://d3js.org/d3.v7.min.js\"></script> "
                "</head> "
                "<body> "
                "    <div id=\"d3-container\"></div> "
                "    <script> "
                "        // D3.js code here "
                "    </script> "
                "</body> "
                "</html>"
            )
            # Simple variant instruction - let LLM be creative
            current_style = style_variant if style_variant else "unique and creative design"

            user_prompt = (
                f"Topic: {prompt.get('topic', '')}\n"
                f"Elements: {prompt.get('elements', '')}\n"
                f"Style: {current_style}\n"
                f"Variant: This is variant {variant_id+1} of 3 - make it unique and different\n"
                f"Instructions: Create a creative and original infographic with COMPLETE HTML structure for headless browser extraction. "
                f"CRITICAL: Use proper HTML structure with DOCTYPE, html, head, body tags. Use forward slashes (/) in closing tags, never backslashes (\\). "
                f"Be innovative with the layout and presentation.\n"
                f"{prompt.get('task', '')}"
            )
            model_with_system = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=system_prompt
            )
            response = model_with_system.generate_content(user_prompt)
            d3_code = response.text.strip()
            
            # Remove accidental markdown code blocks if present
            if d3_code.startswith("```html"):
                d3_code = d3_code[7:]
            if d3_code.startswith("```"):
                d3_code = d3_code[3:]
            if d3_code.endswith("```"):
                d3_code = d3_code[:-3]
            d3_code = d3_code.strip()
            
            # Critical post-processing for headless compatibility
            headless_system_instruction = (
                "You are a D3.js expert and HTML validator specifically focused on headless browser compatibility. "
                "Given HTML+JS code, you must ensure it is perfectly formatted for headless browser extraction: "
                "1. CRITICAL: Fix any backslashes (\\) in closing tags - they must be forward slashes (/) "
                "2. CRITICAL: Fix any backslash comments - use proper /* */ or // comments "
                "3. Ensure complete HTML structure with DOCTYPE, html, head, body tags "
                "4. Ensure proper script tag for D3.js CDN "
                "5. Ensure container div with proper id "
                "6. Fix any syntax errors that would prevent browser rendering "
                "7. Ensure all quotes are properly escaped "
                "8. Ensure no malformed HTML tags "
                "Return ONLY the corrected HTML+JS code, with no explanations or markdown. "
                "The output must be ready for immediate use in a headless browser."
            )
            headless_user_prompt = (
                "Fix this HTML+JS code for headless browser compatibility. "
                "CRITICAL: Replace any backslashes (\\) in closing tags with forward slashes (/). "
                "Fix any syntax errors and ensure proper HTML structure. "
                "Return only the corrected code.\n\n" + d3_code
            )
            headless_model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=headless_system_instruction
            )
            headless_response = headless_model.generate_content(headless_user_prompt)
            headless_fixed_code = headless_response.text.strip()
            
            # Remove accidental markdown code blocks if present
            if headless_fixed_code.startswith("```html"):
                headless_fixed_code = headless_fixed_code[7:]
            if headless_fixed_code.startswith("```"):
                headless_fixed_code = headless_fixed_code[3:]
            if headless_fixed_code.endswith("```"):
                headless_fixed_code = headless_fixed_code[:-3]
            headless_fixed_code = headless_fixed_code.strip()

            # Final validation and cleanup
            final_system_instruction = (
                "You are an HTML validator. "
                "Given HTML code, perform final validation and cleanup: "
                "1. Ensure the HTML starts with <!DOCTYPE html> "
                "2. Ensure proper html, head, body structure "
                "3. Ensure all tags are properly closed with forward slashes (/) "
                "4. Ensure D3.js script is properly loaded "
                "5. Ensure container div exists "
                "6. Fix any remaining syntax issues "
                "Return ONLY the final, clean HTML code with no explanations."
            )
            final_user_prompt = (
                "Perform final validation and cleanup of this HTML code. "
                "Ensure it's ready for headless browser use. "
                "Return only the clean HTML code.\n\n" + headless_fixed_code
            )
            final_model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=final_system_instruction
            )
            final_response = final_model.generate_content(final_user_prompt)
            final_code = final_response.text.strip()
            
            # Remove accidental markdown code blocks if present
            if final_code.startswith("```html"):
                final_code = final_code[7:]
            if final_code.startswith("```"):
                final_code = final_code[3:]
            if final_code.endswith("```"):
                final_code = final_code[:-3]
            final_code = final_code.strip()
            
            return final_code
    
    # Fallback: legacy string prompt flow with headless optimization
    system_prompt = (
        "You are a D3.js expert who creates beautiful, informative, and highly readable single-frame infographics specifically optimized for headless browser extraction. "
        "CRITICAL REQUIREMENTS FOR HEADLESS COMPATIBILITY: "
        "1. You must return COMPLETE, VALID HTML with proper DOCTYPE, html, head, and body tags "
        "2. Use ONLY forward slashes (/) in closing tags - NEVER use backslashes (\\) "
        "3. Use ONLY standard HTML comments (/* */) - NEVER use backslash comments "
        "4. Include proper meta charset and viewport tags "
        "5. Load D3.js from CDN with proper script tags "
        "6. Create a container div with id for D3.js to target "
        "7. All JavaScript must be in proper script tags "
        "You always use correct D3.js and SVG syntax and functions. "
        "You must ONLY return valid HTML+JS code, with NO explanations, NO markdown, and NO ```html or ``` blocks. "
        "The output must be a single static frame (no animation). "
        "All information about the topic must be visible in that single frame. "
        "Text and labels must be well-placed, non-overlapping, and clearly readable. "
        "Include key concepts and explanations with clear, non-crowded diagrams. "
        "Do NOT try to explain in so much detail that the frame becomes crowded or unreadable. "
        "Pay special attention to layout boundaries: No text or element should go outside the visible SVG area or overlap with other elements. "
        "All text and diagram elements must be placed so that they fit within the SVG canvas, with appropriate padding from the edges. "
        "Text labels, section titles, and formulas must not overlap with each other or with diagram elements. Adjust font size, wrapping, or positioning as needed to ensure clarity and no overflow. "
        "If there is not enough space, reduce the number of elements or use ellipsis, but never let text go outside the canvas or overlap."
    )
    user_prompt = (
        f"Create a highly informative and visually engaging single-frame infographic using D3.js with COMPLETE HTML structure for headless browser extraction. "
        f"CRITICAL: Use proper HTML structure with DOCTYPE, html, head, body tags. Use forward slashes (/) in closing tags, never backslashes (\\). "
        f"The output must be a single static frame (no animation) and all information about the topic must be visible in that frame. "
        f"Text and labels must be well-placed, non-overlapping, and clearly readable. "
        f"Include key concepts and explanations with clear, non-crowded diagrams. "
        f"Do NOT try to explain in so much detail that the frame becomes crowded or unreadable. "
        f"Topic: {prompt}"
    )
    model_with_system = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=system_prompt
    )
    response = model_with_system.generate_content(user_prompt)
    d3_code = response.text.strip()
    
    # Apply the same post-processing as above
    # Remove accidental markdown code blocks if present
    if d3_code.startswith("```html"):
        d3_code = d3_code[7:]
    if d3_code.startswith("```"):
        d3_code = d3_code[3:]
    if d3_code.endswith("```"):
        d3_code = d3_code[:-3]
    d3_code = d3_code.strip()
    
    # Apply headless compatibility fixes
    headless_system_instruction = (
        "You are a D3.js expert and HTML validator specifically focused on headless browser compatibility. "
        "Given HTML+JS code, you must ensure it is perfectly formatted for headless browser extraction: "
        "1. CRITICAL: Fix any backslashes (\\) in closing tags - they must be forward slashes (/) "
        "2. CRITICAL: Fix any backslash comments - use proper /* */ or // comments "
        "3. Ensure complete HTML structure with DOCTYPE, html, head, body tags "
        "4. Ensure proper script tag for D3.js CDN "
        "5. Ensure container div with proper id "
        "6. Fix any syntax errors that would prevent browser rendering "
        "Return ONLY the corrected HTML+JS code, with no explanations or markdown."
    )
    headless_user_prompt = (
        "Fix this HTML+JS code for headless browser compatibility. "
        "CRITICAL: Replace any backslashes (\\) in closing tags with forward slashes (/). "
        "Fix any syntax errors and ensure proper HTML structure. "
        "Return only the corrected code.\n\n" + d3_code
    )
    headless_model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=headless_system_instruction
    )
    headless_response = headless_model.generate_content(headless_user_prompt)
    headless_fixed_code = headless_response.text.strip()
    
    # Remove accidental markdown code blocks if present
    if headless_fixed_code.startswith("```html"):
        headless_fixed_code = headless_fixed_code[7:]
    if headless_fixed_code.startswith("```"):
        headless_fixed_code = headless_fixed_code[3:]
    if headless_fixed_code.endswith("```"):
        headless_fixed_code = headless_fixed_code[:-3]
    headless_fixed_code = headless_fixed_code.strip()
    
    return headless_fixed_code