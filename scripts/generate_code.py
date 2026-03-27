import os
import requests
import json
import sys

# Configuration
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
APP_PROMPT = os.environ.get('APP_PROMPT')
SESSION_ID = os.environ.get('SESSION_ID', 'default_session')

def generate_professional_code(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # MASTER SYSTEM PROMPT: Play Store Level App Generation
    system_prompt = """
    You are a Senior Full-Stack Flutter Developer. Your goal is to generate high-quality, production-ready Flutter code.
    
    STRICT RULES:
    1. Output ONLY the raw Dart code for main.dart. No explanations, no markdown backticks.
    2. Use 'flutter/material.dart' and 'dart:math'. No other external packages unless standard.
    3. COMPLEXITY: If the user asks for a big app, create multiple classes for different screens within the same file.
    4. NAVIGATION: Implement professional routing using Navigator 2.0 or simple Navigator push/pop.
    5. DATA PERSISTENCE: Use placeholders for SharedPreferences logic so the user can save data locally.
    6. UI/UX: 
       - Use modern Dark Theme (Color(0xFF0F0F1A)).
       - Add CustomPainter for Charts/Graphs if needed.
       - Use Animations (AnimatedContainer, FadeIn, Scale) for a premium feel.
       - Use Google Fonts style (default sans-serif) with clean spacing.
    7. ERROR HANDLING: Include try-catch blocks for any logic-heavy parts.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-specdec",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a professional Play Store level Flutter app for: {prompt}"}
        ],
        "temperature": 0.7,
        "max_tokens": 8000 # Increased for complex apps
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        print(f"Error: {response.status_code}")
        return None

def main():
    print(f"Building Advanced App for Session: {SESSION_ID}")
    code = generate_professional_code(APP_PROMPT)
    
    if code:
        # Clean the code if AI added markdown
        if "```dart" in code:
            code = code.split("```dart")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
            
        with open("main.dart", "w", encoding="utf-8") as f:
            f.write(code)
        print("Master Code Generated Successfully!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
