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
    
    # MASTER SYSTEM PROMPT: For Play Store Level Apps
    system_prompt = """
    You are a Senior Flutter Architect. Generate a COMPLETE, single-file 'main.dart' app.
    
    STRICT GUIDELINES:
    1. NAVIGATION: If the app needs multiple screens, create multiple classes (e.g., HomeScreen, DetailScreen, SettingsScreen) in the same file. Use Navigator.push for transitions.
    2. STATE MANAGEMENT: Use StatefulWidget and setState effectively to handle complex data.
    3. UI/UX: Use a professional Dark Theme (Color(0xFF0F0F1A)). Use Cards, Gradients, and clean Spacing.
    4. FEATURES: 
       - If requested, add Charts/Graphs using CustomPainter.
       - Add smooth animations using AnimatedContainer or Hero widgets.
       - Use 'dart:convert' and 'shared_preferences' (mock logic) for local data simulation.
    5. PACKAGE LIMIT: Use ONLY 'package:flutter/material.dart', 'dart:math', and 'dart:async'.
    6. OUTPUT: Provide ONLY raw Dart code. No markdown, no backticks, no explanations.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-specdec",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Build a professional multi-screen app for: {prompt}"}
        ],
        "temperature": 0.6,
        "max_tokens": 8000
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print(f"Groq API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    print(f"Building Advanced App: {SESSION_ID}")
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in Environment Variables")
        sys.exit(1)

    code = generate_professional_code(APP_PROMPT)
    
    if code:
        # Cleaning logic to ensure no markdown remains
        if "```dart" in code:
            code = code.split("```dart")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
            
        with open("main.dart", "w", encoding="utf-8") as f:
            f.write(code)
        print("Success: Professional main.dart generated.")
    else:
        print("Failed to generate code.")
        sys.exit(1)

if __name__ == "__main__":
    main()
