#!/usr/bin/env python3
"""
UNIVERSAL AI APP BUILDER v4.0
Generates ANY type of Flutter app (Social, Ecom, Food, Gaming, Utility, etc.)
"""

import os
import subprocess
import re
import shutil
import json
import time
from groq import Groq

# ─── Environment Variables ───────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")
PREVIOUS_CODE = os.environ.get("PREVIOUS_CODE", "")
CONVERSATION_HISTORY = os.environ.get("CONVERSATION_HISTORY", "")
SESSION_ID = os.environ.get("SESSION_ID", "")
APP_COMPLEXITY = os.environ.get("APP_COMPLEXITY", "production")

client = Groq(api_key=GROQ_API_KEY)

# ─── App Type Definitions ─────────────────────────────────────────────────────
APP_TYPES = {
    'social': {
        'name': 'Social Media App',
        'features': ['posts', 'likes', 'comments', 'user profiles', 'follow/unfollow', 'feed', 'stories'],
        'packages': ['http', 'provider', 'cached_network_image', 'image_picker', 'intl'],
        'screens': ['auth', 'feed', 'profile', 'post_details', 'search', 'notifications', 'settings'],
    },
    'ecommerce': {
        'name': 'E-Commerce App',
        'features': ['products', 'categories', 'cart', 'wishlist', 'checkout', 'payment', 'orders', 'reviews'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['home', 'products', 'product_details', 'cart', 'checkout', 'orders', 'profile'],
    },
    'food_delivery': {
        'name': 'Food Delivery App',
        'features': ['restaurants', 'menu', 'cart', 'order tracking', 'location', 'payment', 'ratings'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['home', 'restaurant_details', 'menu', 'cart', 'checkout', 'tracking', 'profile'],
    },
    'fitness': {
        'name': 'Fitness App',
        'features': ['workouts', 'exercises', 'progress tracking', 'calories', 'steps', 'water intake'],
        'packages': ['http', 'provider', 'intl', 'shared_preferences'],
        'screens': ['home', 'workouts', 'exercise_details', 'progress', 'profile', 'settings'],
    },
    'education': {
        'name': 'Education App',
        'features': ['courses', 'lessons', 'quizzes', 'progress', 'certificates', 'videos'],
        'packages': ['http', 'provider', 'video_player', 'cached_network_image', 'intl'],
        'screens': ['home', 'course_details', 'lesson', 'quiz', 'profile', 'certificates'],
    },
    'finance': {
        'name': 'Finance App',
        'features': ['transactions', 'budget', 'expense tracking', 'reports', 'charts', 'savings goals'],
        'packages': ['http', 'provider', 'intl', 'shared_preferences'],
        'screens': ['dashboard', 'transactions', 'budget', 'reports', 'goals', 'profile'],
    },
    'travel': {
        'name': 'Travel App',
        'features': ['destinations', 'hotels', 'bookings', 'reviews', 'itinerary', 'maps'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['home', 'destinations', 'destination_details', 'booking', 'itinerary', 'profile'],
    },
    'healthcare': {
        'name': 'Healthcare App',
        'features': ['appointments', 'doctors', 'medications', 'health records', 'reminders'],
        'packages': ['http', 'provider', 'intl', 'shared_preferences'],
        'screens': ['home', 'doctors', 'appointments', 'medications', 'records', 'profile'],
    },
    'gaming': {
        'name': 'Gaming App',
        'features': ['levels', 'scores', 'leaderboard', 'achievements', 'animations'],
        'packages': ['shared_preferences'],
        'screens': ['home', 'game', 'leaderboard', 'achievements', 'settings'],
    },
    'productivity': {
        'name': 'Productivity App',
        'features': ['tasks', 'notes', 'calendar', 'reminders', 'focus timer', 'categories'],
        'packages': ['http', 'provider', 'intl', 'shared_preferences'],
        'screens': ['dashboard', 'tasks', 'notes', 'calendar', 'focus', 'profile'],
    },
}

# ─── System Prompt ────────────────────────────────────────────────────────────
def get_system_prompt(app_type: str, complexity: str) -> str:
    type_info = APP_TYPES.get(app_type, APP_TYPES['ecommerce'])
    
    return f"""You are a world-class Flutter developer. Create a COMPLETE, PRODUCTION-READY {type_info['name']}.

════════════════════════════════════════
APP REQUIREMENTS:
════════════════════════════════════════
Type: {type_info['name']}
Complexity: {complexity.upper()}
Features: {', '.join(type_info['features'])}
Screens: {', '.join(type_info['screens'])}

════════════════════════════════════════
PROJECT STRUCTURE:
════════════════════════════════════════

lib/
├── main.dart
├── screens/ (all screens)
├── widgets/ (reusable widgets)
├── models/ (data models)
├── providers/ (state management)
├── services/ (API services)
├── utils/ (constants, helpers)
└── themes/ (app theme)

════════════════════════════════════════
RULES:
════════════════════════════════════════

1. Use Material 3 with dark theme (primary: #6C63FF)
2. Use Provider for state management
3. Create separate files for each screen
4. Add proper error handling and loading states
5. Use mock data if no API provided
6. Make it beautiful with animations
7. All text must have explicit white color
8. Include all necessary imports

════════════════════════════════════════
OUTPUT FORMAT:
════════════════════════════════════════

===FILE: lib/main.dart===
[complete code]

===FILE: lib/screens/home_screen.dart===
[complete code]

===FILE: lib/models/item_model.dart===
[complete code]

===FILE: lib/providers/app_provider.dart===
[complete code]

... (all files)

Return ONLY the code files with ===FILE: markers. No explanations."""


def detect_app_type(prompt: str) -> str:
    lower = prompt.lower()
    
    if any(w in lower for w in ['social', 'instagram', 'facebook', 'post', 'feed']):
        return 'social'
    if any(w in lower for w in ['ecommerce', 'shop', 'store', 'product', 'cart']):
        return 'ecommerce'
    if any(w in lower for w in ['food', 'delivery', 'restaurant', 'menu', 'order']):
        return 'food_delivery'
    if any(w in lower for w in ['fitness', 'gym', 'workout', 'exercise']):
        return 'fitness'
    if any(w in lower for w in ['education', 'course', 'quiz', 'learning']):
        return 'education'
    if any(w in lower for w in ['finance', 'bank', 'expense', 'budget']):
        return 'finance'
    if any(w in lower for w in ['travel', 'hotel', 'booking', 'trip']):
        return 'travel'
    if any(w in lower for w in ['healthcare', 'doctor', 'appointment']):
        return 'healthcare'
    if any(w in lower for w in ['game', 'gaming', 'play']):
        return 'gaming'
    if any(w in lower for w in ['todo', 'task', 'note', 'productivity']):
        return 'productivity'
    
    return 'ecommerce'


def call_groq_with_retry(messages, model, temperature, max_tokens, max_retries=3):
    for i in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            if "rate_limit" in str(e).lower() and i < max_retries - 1:
                wait = 2 ** i
                print(f"  ⏳ Rate limit, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")


def parse_multi_file_code(output: str) -> dict:
    files = {}
    current_file = None
    current_content = []
    
    lines = output.split('\n')
    for line in lines:
        file_match = re.match(r'^===FILE:\s*(.+?)\s*===', line)
        if file_match:
            if current_file:
                files[current_file] = '\n'.join(current_content).strip()
            current_file = file_match.group(1).strip()
            current_content = []
        else:
            if current_file:
                current_content.append(line)
    
    if current_file:
        files[current_file] = '\n'.join(current_content).strip()
    
    return files


def generate_pubspec(app_type: str) -> str:
    type_info = APP_TYPES.get(app_type, APP_TYPES['ecommerce'])
    deps = ['provider', 'http', 'shared_preferences', 'intl', 'cached_network_image']
    
    deps_yaml = '\n'.join([f'  {dep}: ^1.0.0' for dep in deps if dep != 'flutter'])
    
    return f'''name: ai_generated_app
description: AI Generated Flutter App
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
{deps_yaml}

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
'''


def generate_theme() -> str:
    return '''import 'package:flutter/material.dart';

class AppTheme {
  static final ThemeData darkTheme = ThemeData(
    brightness: Brightness.dark,
    useMaterial3: true,
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF6C63FF),
      secondary: Color(0xFF03DAC6),
      background: Color(0xFF0F0F1A),
      surface: Color(0xFF1E1E2E),
    ),
    scaffoldBackgroundColor: const Color(0xFF0F0F1A),
    cardTheme: CardTheme(
      color: const Color(0xFF1E1E2E),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF6C63FF),
        minimumSize: const Size(double.infinity, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
  );
}
'''


def create_project_from_files(files: dict, project_name: str = "generated_app"):
    if os.path.exists(project_name):
        shutil.rmtree(project_name)
    
    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder",
         "--project-name", project_name, project_name],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise Exception(f"Flutter create failed: {result.stderr}")
    
    for filepath, content in files.items():
        if filepath == 'pubspec.yaml':
            full_path = os.path.join(project_name, filepath)
        else:
            full_path = os.path.join(project_name, filepath)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)


def generate_universal_code(prompt: str, previous_code: str = "", attempt: int = 1) -> dict:
    app_type = detect_app_type(prompt)
    type_info = APP_TYPES.get(app_type, APP_TYPES['ecommerce'])
    
    print(f"  📱 App Type: {type_info['name']}")
    print(f"  ⭐ Features: {', '.join(type_info['features'][:4])}")
    
    complexity = "production" if attempt == 1 else ("medium" if attempt == 2 else "simple")
    
    system_prompt = get_system_prompt(app_type, complexity)
    
    if previous_code and previous_code.strip():
        user_prompt = f"""MODIFY this existing app:

USER REQUEST: {prompt}

EXISTING CODE:
{previous_code}

Return COMPLETE updated code for ALL files in the ===FILE: path=== format."""
    else:
        user_prompt = f"""Create a COMPLETE, PRODUCTION-READY {type_info['name']}:

USER REQUEST: {prompt}

Features required: {', '.join(type_info['features'])}
Screens required: {', '.join(type_info['screens'])}

Return ALL files in the ===FILE: path=== format."""
    
    response = call_groq_with_retry(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=10000,
    )
    
    output = response.choices[0].message.content.strip()
    files = parse_multi_file_code(output)
    
    # Add essential files if missing
    if 'pubspec.yaml' not in files:
        files['pubspec.yaml'] = generate_pubspec(app_type)
    
    if 'lib/themes/app_theme.dart' not in files:
        files['lib/themes/app_theme.dart'] = generate_theme()
    
    return files


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("🚀 UNIVERSAL AI APP BUILDER v4.0")
    print("   Build ANY App - Social, Ecom, Food, Gaming, etc.")
    print("=" * 55)
    print(f"📝 Prompt: {APP_PROMPT[:100]}")
    
    app_type = detect_app_type(APP_PROMPT)
    print(f"🎯 Type: {APP_TYPES[app_type]['name']}")
    
    final_files = None
    
    for attempt in range(1, 4):
        print(f"\n{'━'*20} Attempt {attempt}/3 {'━'*20}")
        try:
            files = generate_universal_code(APP_PROMPT, PREVIOUS_CODE, attempt)
            print(f"📁 Generated {len(files)} files")
            
            create_project_from_files(files)
            
            print("\n🔨 Building APK...")
            result = subprocess.run(
                ["flutter", "build", "apk", "--release"],
                cwd="generated_app",
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("\n" + "=" * 55)
                print("🎉 APK BUILD SUCCESSFUL!")
                print("=" * 55)
                print("📱 APK: generated_app/build/app/outputs/flutter-apk/app-release.apk")
                final_files = files
                break
            else:
                print(f"❌ Build failed. Retrying...")
                PREVIOUS_CODE = "\n".join(files.values())
                
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    if not final_files:
        raise Exception("❌ Could not build APK after all attempts")
    
    # Save final code
    with open("final_code.dart", "w", encoding='utf-8') as f:
        for path, content in final_files.items():
            f.write(f"\n// FILE: {path}\n")
            f.write(content)
            f.write("\n\n")
    
    print("\n✅ Done!")
