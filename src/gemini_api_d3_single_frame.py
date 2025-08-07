def get_d3_code_single_frame(prompt):
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
            # Step 2: Generate code for the given elements
            system_prompt = (
                "You are a D3.js expert who creates beautiful, informative, and highly readable single-frame infographics. "
                "You must ONLY use valid D3.js (v7+) and SVG syntax and functions—do not use any syntax, classes, or methods that are not part of the official D3.js or SVG specification. "
                "You must ONLY return valid HTML+JS code, with NO explanations, NO markdown, and NO ```html or ``` blocks. "
                "The output must be a single static frame (no animation unless requested). "
                "All information about the topic must be visible in that single frame. "
                "Text and labels must be well-placed, non-overlapping, and clearly readable. "
                "Include key concepts and explanations with clear, non-crowded diagrams. "
                "Do NOT use any custom or undefined classes, functions, or imports. "
                "Do NOT try to explain in so much detail that the frame becomes crowded or unreadable. "
                "Use ONLY the provided elements. "
                "IMPORTANT SIZING CONSTRAINTS: Create SVG with dimensions that fit comfortably on standard screens. "
                "Recommended SVG size: width=800-1000px, height=600-800px maximum. Avoid creating very tall infographics (>900px height) that require excessive scrolling. "
                "Design for landscape orientation when possible. If content requires more height, use compact layouts, smaller fonts, or multi-column arrangements. "
                "Pay special attention to layout boundaries: No text or element should go outside the visible SVG area or overlap with other elements. "
                "All text and diagram elements must be placed so that they fit within the SVG canvas, with appropriate padding from the edges. "
                "Text labels, section titles, and formulas must not overlap with each other or with diagram elements. Adjust font size, wrapping, or positioning as needed to ensure clarity and no overflow. "
                "If there is not enough space, reduce the number of elements, use smaller fonts, or create a more compact layout, but never let text go outside the canvas or overlap."
            )
            user_prompt = (
                f"Topic: {prompt.get('topic', '')}\n"
                f"Elements: {prompt.get('elements', '')}\n"
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
            # Post-process: Ask Gemini to check for overlapping elements and fix them
            post_system_instruction = (
                "You are a D3.js expert and code reviewer. "
                "Given a D3.js HTML+JS code for a single-frame infographic, "
                "analyze the code for any overlapping or crowded text or elements. "
                "If you find overlapping or crowded elements, fix the code by repositioning, resizing, "
                "or removing some information as needed, but ensure the infographic remains clear, readable, "
                "and still makes sense. "
                "If you remove information, prioritize keeping the most important key concepts. "
                "Return ONLY the fixed HTML+JS code, with no explanations or markdown. "
            )
            post_user_prompt = (
                "Here is the D3.js code for a single-frame infographic. "
                "Check for overlapping or crowded elements and fix them as needed. "
                "If you must remove information, keep the most important key concepts. "
                "Return only the fixed code.\n\n" + d3_code
            )
            post_model_with_system = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=post_system_instruction
            )
            post_response = post_model_with_system.generate_content(post_user_prompt)
            fixed_code = post_response.text.strip()
            # Remove accidental markdown code blocks if present
            if fixed_code.startswith("```html"):
                fixed_code = fixed_code[7:]
            if fixed_code.startswith("```"):
                fixed_code = fixed_code[3:]
            if fixed_code.endswith("```"):
                fixed_code = fixed_code[:-3]
            fixed_code = fixed_code.strip()

            # Second post-process: Ask Gemini to check and fix D3.js/HTML syntax errors
            syntax_system_instruction = (
                "You are a D3.js expert and code reviewer. "
                "Given a D3.js HTML+JS code, check for any D3.js or HTML syntax errors or issues. "
                "Fix all syntax errors and return ONLY the corrected HTML+JS code, with no explanations or markdown. "
            )
            syntax_user_prompt = (
                "Here is the D3.js code. Check for any syntax errors and fix them. "
                "Return only the corrected code.\n\n" + fixed_code
            )
            syntax_model_with_system = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=syntax_system_instruction
            )
            syntax_response = syntax_model_with_system.generate_content(syntax_user_prompt)
            syntax_fixed_code = syntax_response.text.strip()
            # Remove accidental markdown code blocks if present
            if syntax_fixed_code.startswith("```html"):
                syntax_fixed_code = syntax_fixed_code[7:]
            if syntax_fixed_code.startswith("```"):
                syntax_fixed_code = syntax_fixed_code[3:]
            if syntax_fixed_code.endswith("```"):
                syntax_fixed_code = syntax_fixed_code[:-3]
            syntax_fixed_code = syntax_fixed_code.strip()
            return syntax_fixed_code
    # Fallback: legacy string prompt flow
    # ...existing code for legacy string prompt...
    system_prompt = (
        "You are a D3.js expert who creates beautiful, informative, and highly readable single-frame infographics. "
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
        f"Create a highly informative and visually engaging single-frame infographic using D3.js. "
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
    # Remove accidental markdown code blocks if present
    if d3_code.startswith("```html"):
        d3_code = d3_code[7:]
    if d3_code.startswith("```"):
        d3_code = d3_code[3:]
    if d3_code.endswith("```"):
        d3_code = d3_code[:-3]
    d3_code = d3_code.strip()
    # Post-process: Ask Gemini to check for overlapping elements and fix them
    post_system_instruction = (
        "You are a D3.js expert and code reviewer. "
        "Given a D3.js HTML+JS code for a single-frame infographic, "
        "analyze the code for any overlapping or crowded text or elements. "
        "If you find overlapping or crowded elements, fix the code by repositioning, resizing, "
        "or removing some information as needed, but ensure the infographic remains clear, readable, "
        "and still makes sense. "
        "If you remove information, prioritize keeping the most important key concepts. "
        "Return ONLY the fixed HTML+JS code, with no explanations or markdown. "
    )
    post_user_prompt = (
        "Here is the D3.js code for a single-frame infographic. "
        "Check for overlapping or crowded elements and fix them as needed. "
        "If you must remove information, keep the most important key concepts. "
        "Return only the fixed code.\n\n" + d3_code
    )
    post_model_with_system = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=post_system_instruction
    )
    post_response = post_model_with_system.generate_content(post_user_prompt)
    fixed_code = post_response.text.strip()
    # Remove accidental markdown code blocks if present
    if fixed_code.startswith("```html"):
        fixed_code = fixed_code[7:]
    if fixed_code.startswith("```"):
        fixed_code = fixed_code[3:]
    if fixed_code.endswith("```"):
        fixed_code = fixed_code[:-3]
    fixed_code = fixed_code.strip()

    # Second post-process: Ask Gemini to check and fix D3.js/HTML syntax errors
    syntax_system_instruction = (
        "You are a D3.js expert and code reviewer. "
        "Given a D3.js HTML+JS code, check for any D3.js or HTML syntax errors or issues. "
        "Fix all syntax errors and return ONLY the corrected HTML+JS code, with no explanations or markdown. "
    )
    syntax_user_prompt = (
        "Here is the D3.js code. Check for any syntax errors and fix them. "
        "Return only the corrected code.\n\n" + fixed_code
    )
    syntax_model_with_system = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=syntax_system_instruction
    )
    syntax_response = syntax_model_with_system.generate_content(syntax_user_prompt)
    syntax_fixed_code = syntax_response.text.strip()
    # Remove accidental markdown code blocks if present
    if syntax_fixed_code.startswith("```html"):
        syntax_fixed_code = syntax_fixed_code[7:]
    if syntax_fixed_code.startswith("```"):
        syntax_fixed_code = syntax_fixed_code[3:]
    if syntax_fixed_code.endswith("```"):
        syntax_fixed_code = syntax_fixed_code[:-3]
    syntax_fixed_code = syntax_fixed_code.strip()
    return syntax_fixed_code
