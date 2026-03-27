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
    
    # MASTER SYSTEM PROMPT: Designed for High-Level Apps
    system_prompt = """
    You are a Senior Flutter Developer specializing in Play Store apps. 
    Your task is to generate a SINGLE-FILE Flutter app that is sophisticated and professional.

    CORE REQUIREMENTS:
    1. MULTI-SCREEN: If the app is complex (e.g., E-commerce, Fitness Tracker), include at least 3 screens (Home, Detail, Profile) using Navigator.push.
    2. STATE MANAGEMENT: Use advanced StatefulWidget logic to manage data across screens.
    3. PROFESSIONAL UI:
       - Use a premium Dark Theme (Background: 0xFF0F0F1A).
       - Use custom Gradients and Rounded Cards (BorderRadius.circular(20)).
       - Add clean Padding and Spacing (SizedBox).
    4. DATA SIMULATION: Implement functions to save/load data using JSON logic (simulating local database).
    5. VISUALS & CHARTS: 
       - If the app needs statistics, draw custom Charts using 'CustomPainter'.
       - Use 'dart:math' for calculations.
    6. ANIMATIONS: Add smooth transitions using 'AnimatedContainer', 'Hero', and 'Opacity' animations.
    7. NO EXTERNAL PACKAGES: Use ONLY 'flutter/material.dart', 'dart:math', and 'dart:convert'.

    OUTPUT: Provide ONLY the raw Dart code. No text, no markdown backticks.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-specdec",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Build a complex, multi-screen professional app for: {prompt}"}
        ],
        "temperature": 0.65,
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
    print(f"Starting Generation for: {SESSION_ID}")
    if not GROQ_API_KEY:
        print("Error: Missing GROQ_API_KEY")
        sys.exit(1)

    code = generate_professional_code(APP_PROMPT)
    
    if code:
        # Strict Cleaning: Removing any possible AI conversational text
        if "```dart" in code:
            code = code.split("```dart")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
            
        with open("main.dart", "w", encoding="utf-8") as f:
            f.write(code)
        print("Success: Professional main.dart created.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
