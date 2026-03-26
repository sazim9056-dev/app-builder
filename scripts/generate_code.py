#!/usr/bin/env python3
"""
UNIVERSAL AI APP BUILDER v4.1 - Fixed App Type Detection
"""

import os
import subprocess
import re
import shutil
import json
import time
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")
PREVIOUS_CODE = os.environ.get("PREVIOUS_CODE", "")
CONVERSATION_HISTORY = os.environ.get("CONVERSATION_HISTORY", "")
SESSION_ID = os.environ.get("SESSION_ID", "")
APP_COMPLEXITY = os.environ.get("APP_COMPLEXITY", "production")

client = Groq(api_key=GROQ_API_KEY)

# ─── IMPROVED App Type Detection ─────────────────────────────────────────────
def detect_app_type(prompt):
    lower = prompt.lower()
    
    # Calculator / Simple Utility Apps (High Priority)
    if any(w in lower for w in ['calculator', 'calc', 'bmi', 'emi', 'sip', 'todo', 'task', 'note', 'timer', 'stopwatch', 'converter', 'unit converter', 'password', 'random', 'age calculator', 'countdown']):
        return 'utility'
    
    # Social Media
    if any(w in lower for w in ['social', 'instagram', 'facebook', 'twitter', 'post', 'feed', 'story', 'chat', 'whatsapp']):
        return 'social'
    
    # E-Commerce
    if any(w in lower for w in ['ecommerce', 'shop', 'store', 'product', 'cart', 'checkout', 'sell', 'shopping', 'amazon', 'flipkart']):
        return 'ecommerce'
    
    # Food Delivery
    if any(w in lower for w in ['food', 'delivery', 'restaurant', 'hotel', 'menu', 'order', 'zomato', 'swiggy']):
        return 'food_delivery'
    
    # Fitness
    if any(w in lower for w in ['fitness', 'gym', 'workout', 'exercise', 'step', 'calorie', 'health', 'weight', 'bmi']):
        return 'fitness'
    
    # Education
    if any(w in lower for w in ['education', 'learning', 'course', 'quiz', 'school', 'student', 'teacher', 'lesson']):
        return 'education'
    
    # Finance
    if any(w in lower for w in ['finance', 'bank', 'expense', 'budget', 'money', 'investment', 'stock', 'crypto', 'emi', 'sip']):
        return 'finance'
    
    # Travel
    if any(w in lower for w in ['travel', 'trip', 'hotel', 'flight', 'booking', 'tour', 'vacation']):
        return 'travel'
    
    # Gaming
    if any(w in lower for w in ['game', 'gaming', 'play', 'score', 'level', 'quiz game']):
        return 'gaming'
    
    # Default
    return 'utility'  # Simple utility app by default

# ─── App Type Configurations ─────────────────────────────────────────────────
APP_TYPES = {
    'utility': {
        'name': 'Utility App',
        'features': ['simple UI', 'basic calculations', 'clean design', 'dark theme'],
        'packages': ['provider', 'intl', 'shared_preferences'],
        'screens': ['home'],
        'complexity': 'simple',
        'description': 'Create a simple, clean calculator/utility app with dark theme'
    },
    'social': {
        'name': 'Social Media App',
        'features': ['posts', 'likes', 'comments', 'user profiles'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['auth', 'feed', 'profile', 'post_details'],
        'complexity': 'complex',
    },
    'ecommerce': {
        'name': 'E-Commerce App',
        'features': ['products', 'categories', 'cart', 'checkout'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['home', 'products', 'product_details', 'cart', 'profile'],
        'complexity': 'complex',
    },
    'food_delivery': {
        'name': 'Food Delivery App',
        'features': ['restaurants', 'menu', 'cart', 'order tracking'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['home', 'restaurant_details', 'cart', 'tracking'],
        'complexity': 'complex',
    },
    'fitness': {
        'name': 'Fitness App',
        'features': ['workouts', 'progress tracking', 'calories'],
        'packages': ['http', 'provider', 'intl', 'shared_preferences'],
        'screens': ['home', 'workouts', 'progress', 'profile'],
        'complexity': 'medium',
    },
    'education': {
        'name': 'Education App',
        'features': ['courses', 'lessons', 'quizzes'],
        'packages': ['http', 'provider', 'video_player', 'intl'],
        'screens': ['home', 'course_details', 'quiz', 'profile'],
        'complexity': 'complex',
    },
    'finance': {
        'name': 'Finance App',
        'features': ['transactions', 'budget', 'expense tracking', 'charts'],
        'packages': ['http', 'provider', 'intl', 'shared_preferences'],
        'screens': ['dashboard', 'transactions', 'budget', 'reports'],
        'complexity': 'medium',
    },
    'travel': {
        'name': 'Travel App',
        'features': ['destinations', 'bookings', 'reviews', 'itinerary'],
        'packages': ['http', 'provider', 'cached_network_image', 'intl'],
        'screens': ['home', 'destinations', 'booking', 'profile'],
        'complexity': 'complex',
    },
    'gaming': {
        'name': 'Gaming App',
        'features': ['levels', 'scores', 'leaderboard'],
        'packages': ['shared_preferences'],
        'screens': ['home', 'game', 'leaderboard'],
        'complexity': 'simple',
    },
}

# ─── System Prompt for Utility Apps (Calculator, Todo, etc.) ─────────────────
def get_utility_system_prompt(prompt, complexity):
    return f"""You are a Flutter developer. Create a SIMPLE, WORKING {prompt}.

APP: {prompt}

ABSOLUTE RULES:
1. Create a SINGLE SCREEN app (StatefulWidget)
2. Use ONLY flutter/material.dart - NO external packages
3. Dark theme with primary color #6C63FF
4. Background: Color(0xFF0F0F1A)
5. All text: Colors.white
6. Use setState() for state management
7. Make it functional and clean

OUTPUT FORMAT (SINGLE FILE):
===FILE: lib/main.dart===
[complete code with main() and HomeScreen]

Return ONLY the code. No explanations."""

def get_complex_system_prompt(app_type, complexity):
    type_info = APP_TYPES.get(app_type, APP_TYPES['utility'])
    
    return f"""You are a Flutter developer. Create a {type_info['name']}.

APP TYPE: {type_info['name']}
FEATURES: {', '.join(type_info['features'])}
COMPLEXITY: {complexity}

RULES:
1. Use Material 3 with dark theme (#6C63FF primary)
2. Use Provider for state management if complex
3. Create separate files for screens
4. Add error handling and loading states
5. All text must be white

OUTPUT FORMAT:
===FILE: lib/main.dart===
[code]
===FILE: lib/screens/home_screen.dart===
[code]

Return ONLY code files."""

# ─── Generate Code ───────────────────────────────────────────────────────────
def generate_code(prompt, previous_code="", attempt=1):
    app_type = detect_app_type(prompt)
    type_info = APP_TYPES.get(app_type, APP_TYPES['utility'])
    
    print(f"  📱 App Type: {type_info['name']}")
    
    # For simple apps (calculator, todo, etc.) use simple prompt
    if app_type == 'utility':
        complexity = "simple"
        system_prompt = get_utility_system_prompt(prompt, complexity)
    else:
        complexity = "simple" if attempt >= 2 else "medium"
        system_prompt = get_complex_system_prompt(app_type, complexity)
    
    if previous_code and previous_code.strip():
        user_prompt = f"""MODIFY this app:

REQUEST: {prompt}

EXISTING CODE:
{previous_code}

Return updated code in the same format."""
    else:
        user_prompt = f"""Create this app: {prompt}
Make it clean, functional, and working."""
    
    try:
        response = call_groq_with_retry(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=6000,
        )
        
        output = response.choices[0].message.content.strip()
        files = parse_multi_file_code(output)
        
        # Add essential files if missing
        if not files:
            files = {'lib/main.dart': output}
        
        # Add pubspec.yaml if missing
        if 'pubspec.yaml' not in files:
            files['pubspec.yaml'] = generate_simple_pubspec()
        
        # Add theme if missing and needed
        if 'lib/themes/app_theme.dart' not in files and app_type != 'utility':
            files['lib/themes/app_theme.dart'] = generate_theme()
        
        return files
        
    except Exception as e:
        print(f"  ❌ Generation error: {e}")
        # Fallback: generate a simple working app
        return generate_fallback_app(prompt)

def generate_fallback_app(prompt):
    """Generate a simple working app if AI fails"""
    print("  ⚡ Using fallback - generating simple working app")
    
    main_dart = f'''import 'package:flutter/material.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: 'AI App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF6C63FF),
          background: Color(0xFF0F0F1A),
        ),
        scaffoldBackgroundColor: const Color(0xFF0F0F1A),
      ),
      home: const HomeScreen(),
    );
  }}
}}

class HomeScreen extends StatefulWidget {{
  const HomeScreen({{super.key}});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}}

class _HomeScreenState extends State<HomeScreen> {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{prompt[:30]}'),
        centerTitle: true,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.android,
                size: 80,
                color: Color(0xFF6C63FF),
              ),
              const SizedBox(height: 20),
              const Text(
                'App Ready!',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              Text(
                'Your app has been generated successfully.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white70),
              ),
            ],
          ),
        ),
      ),
    );
  }}
}}
'''
    return {'lib/main.dart': main_dart, 'pubspec.yaml': generate_simple_pubspec()}

def generate_simple_pubspec():
    return '''name: ai_app
description: AI Generated App
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

dev_dependencies:
  flutter_test:
    sdk: flutter

flutter:
  uses-material-design: true
'''

def generate_theme():
    return '''import 'package:flutter/material.dart';

class AppTheme {
  static final ThemeData darkTheme = ThemeData(
    brightness: Brightness.dark,
    useMaterial3: true,
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF6C63FF),
      background: Color(0xFF0F0F1A),
      surface: Color(0xFF1E1E2E),
    ),
    scaffoldBackgroundColor: const Color(0xFF0F0F1A),
  );
}
'''

def parse_multi_file_code(output):
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

def create_project_from_files(files, project_name="generated_app"):
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
        full_path = os.path.join(project_name, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("🚀 UNIVERSAL AI APP BUILDER v4.1")
    print("=" * 55)
    print(f"📝 Prompt: {APP_PROMPT[:100]}")
    
    app_type = detect_app_type(APP_PROMPT)
    print(f"🎯 Detected Type: {APP_TYPES.get(app_type, APP_TYPES['utility'])['name']}")
    
    final_files = None
    
    for attempt in range(1, 4):
        print(f"\n{'━'*20} Attempt {attempt}/3 {'━'*20}")
        try:
            files = generate_code(APP_PROMPT, PREVIOUS_CODE, attempt)
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
                final_files = files
                break
            else:
                print(f"❌ Build failed. Error: {result.stderr[-500:]}")
                PREVIOUS_CODE = "\n".join(files.values())
                
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    if not final_files:
        raise Exception("❌ Could not build APK after all attempts")
    
    print("\n✅ Done!")
