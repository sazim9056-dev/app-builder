import os
import subprocess
import re
import shutil
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

client = Groq(api_key=GROQ_API_KEY)

# =============================================
# KNOWN ERRORS AUTO-FIX DATABASE
# Jab bhi naya error aaye, yahan add karo
# =============================================
KNOWN_FIXES = {
    'Icons.google': 'Icons.language',
    'Icons.facebook': 'Icons.thumb_up',
    'Icons.twitter': 'Icons.tag',
    'Icons.instagram': 'Icons.camera_alt',
    'Icons.apple': 'Icons.phone_iphone',
    'Icons.whatsapp': 'Icons.chat',
    'Icons.youtube': 'Icons.play_circle',
    'Icons.github': 'Icons.code',
    'Icons.microsoft': 'Icons.window',
    'Icons.linkedin': 'Icons.work',
}


# =============================================
# STEP 1: CODE GENERATE KARO
# =============================================
def generate_flutter_code(prompt: str, attempt: int = 1) -> str:
    print(f"  Generating code (attempt {attempt})...")

    extra = ""
    if attempt == 2:
        extra = "SIMPLIFY: Use only basic widgets - Text, Container, Column, Row, ElevatedButton, Scaffold, AppBar, BottomNavigationBar, ListView, Card."
    elif attempt >= 3:
        extra = "MAKE IT VERY SIMPLE: Single screen only. Basic list of information. No navigation, no complex widgets."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an expert Flutter developer. Generate ONLY valid, compilable Dart code.

RULES:
1. Start EXACTLY with: import 'package:flutter/material.dart';
2. Must have: void main() => runApp(const MyApp());
3. ONLY built-in Flutter/Material widgets
4. NO external packages ever
5. Dark theme template (copy exactly):
   theme: ThemeData(
     brightness: Brightness.dark,
     colorScheme: ColorScheme.fromSeed(
       seedColor: Colors.blue,
       brightness: Brightness.dark,
     ),
     useMaterial3: true,
   ),
6. Light theme template:
   theme: ThemeData(
     colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
     useMaterial3: true,
   ),
7. VALID Icons only: Icons.home, Icons.search, Icons.person, Icons.settings,
   Icons.email, Icons.lock, Icons.visibility, Icons.visibility_off,
   Icons.add, Icons.delete, Icons.edit, Icons.check, Icons.close,
   Icons.arrow_back, Icons.menu, Icons.star, Icons.favorite,
   Icons.language, Icons.phone, Icons.camera_alt, Icons.image,
   Icons.notifications, Icons.logout, Icons.login, Icons.account_circle,
   Icons.fitness_center, Icons.directions_run, Icons.local_fire_department,
   Icons.water_drop, Icons.bar_chart, Icons.timeline, Icons.restaurant
8. NEVER use: Icons.google, Icons.facebook, Icons.twitter, Icons.apple
9. NEVER use: accentColor, primarySwatch, fl_chart, any external package
10. ALL Text in dark theme MUST have color: TextStyle(color: Colors.white)
11. NO markdown, NO backticks - ONLY pure Dart code"""
            },
            {
                "role": "user",
                "content": f"Create Flutter app: {prompt}\n\n{extra}"
            }
        ],
        temperature=0.1 if attempt == 1 else 0.05,
        max_tokens=4000,
    )

    code = response.choices[0].message.content.strip()

    # Clean markdown
    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    # Fix start
    if not code.startswith("import"):
        idx = code.find("import 'package:flutter/material.dart'")
        if idx != -1:
            code = code[idx:]

    return code


# =============================================
# STEP 2: KNOWN ERRORS AUTO-FIX
# =============================================
def apply_known_fixes(code: str) -> str:
    # Fix known bad icons
    for wrong, correct in KNOWN_FIXES.items():
        code = code.replace(wrong, correct)

    # Fix bad packages
    bad_packages = [
        'fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
        'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
        'vector_math', 'syncfusion', 'get:', 'riverpod', 'intl',
        'shared_preferences', 'path_provider', 'image_picker',
        'flutter_svg', 'cached_network_image', 'lottie'
    ]
    for pkg in bad_packages:
        code = re.sub(rf"import 'package:{pkg}[^']*';\n?", '', code)

    # Fix accentColor (deprecated)
    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)

    # Fix primarySwatch (deprecated)
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,',
        code
    )

    # Fix ColorScheme.fromSwatch (old API)
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )

    # Fix brightness mismatch
    if 'brightness: Brightness.dark' in code:
        code = re.sub(
            r'ColorScheme\.fromSeed\(\s*seedColor\s*:\s*(Colors\.\w+)\s*\)',
            r'ColorScheme.fromSeed(seedColor: \1, brightness: Brightness.dark)',
            code
        )

    # Fix Transform matrix errors
    code = re.sub(r'transform\s*:\s*Transform\.[^,\n]+,?\n?', '', code)
    code = re.sub(r'transform\s*:\s*Matrix4[^,\n]+,?\n?', '', code)
    code = re.sub(r"import 'package:vector_math[^']*';\n?", '', code)

    # Fix missing colorScheme
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true, '
        )

    return code


# =============================================
# STEP 3: AI SE ERROR FIX KARWAO (SELF-REPAIR)
# =============================================
def ai_fix_errors(code: str, errors: list) -> str:
    print(f"  🔧 AI self-repairing {len(errors)} error(s)...")

    error_text = '\n'.join(errors)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a Flutter debugging expert. Fix the given Dart code errors.

RULES:
1. Return ONLY the fixed Dart code - no explanations
2. Fix ALL errors listed
3. Keep the app functionality same
4. NO external packages
5. NO markdown or backticks
6. ONLY valid Flutter/Material widgets"""
            },
            {
                "role": "user",
                "content": f"""Fix these Flutter errors:

ERRORS:
{error_text}

ORIGINAL CODE:
{code}

Return the complete fixed Dart code only."""
            }
        ],
        temperature=0.05,
        max_tokens=4000,
    )

    fixed_code = response.choices[0].message.content.strip()

    # Clean markdown
    if "```dart" in fixed_code:
        fixed_code = fixed_code.split("```dart")[1].split("```")[0].strip()
    elif "```" in fixed_code:
        fixed_code = fixed_code.split("```")[1].split("```")[0].strip()

    # Fix start
    if not fixed_code.startswith("import"):
        idx = fixed_code.find("import 'package:flutter/material.dart'")
        if idx != -1:
            fixed_code = fixed_code[idx:]

    # Apply known fixes again
    fixed_code = apply_known_fixes(fixed_code)

    print("  ✅ AI fix applied!")
    return fixed_code


# =============================================
# STEP 4: PROJECT BANAO
# =============================================
def create_project(code: str, project_name: str = "generated_app"):
    if os.path.exists(project_name):
        shutil.rmtree(project_name)

    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder",
         "--project-name", project_name, project_name],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise Exception(f"Flutter create failed: {result.stderr}")

    with open(os.path.join(project_name, "lib", "main.dart"), 'w') as f:
        f.write(code)

    subprocess.run(
        ["flutter", "pub", "get"],
        cwd=project_name,
        capture_output=True, timeout=120
    )


# =============================================
# STEP 5: VALIDATE - ERRORS NIKALO
# =============================================
def get_errors(project_name: str) -> list:
    result = subprocess.run(
        ["flutter", "analyze", "--no-congratulate"],
        cwd=project_name,
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    errors = []
    for line in output.split('\n'):
        if 'error •' in line.lower():
            errors.append(line.strip())
    return errors


# =============================================
# STEP 6: APK BUILD KARO
# =============================================
def build_apk(project_name: str) -> tuple[bool, list]:
    result = subprocess.run(
        ["flutter", "build", "apk", "--debug"],
        cwd=project_name,
        capture_output=True, text=True, timeout=600
    )

    if result.returncode == 0:
        return True, []

    # Build errors extract karo
    build_errors = []
    for line in result.stderr.split('\n'):
        if 'error:' in line.lower() and 'lib/' in line:
            build_errors.append(line.strip())

    return False, build_errors


# =============================================
# MAIN: SELF-HEALING PIPELINE
# =============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 SELF-HEALING AI APP BUILDER")
    print("=" * 50)
    print(f"📝 Prompt: {APP_PROMPT[:80]}...")
    print()

    MAX_GENERATE_ATTEMPTS = 3
    MAX_FIX_ATTEMPTS = 5  # Har generate ke baad 5 fix attempts
    
    final_success = False

    for gen_attempt in range(1, MAX_GENERATE_ATTEMPTS + 1):
        print(f"━━━ GENERATION ATTEMPT {gen_attempt}/{MAX_GENERATE_ATTEMPTS} ━━━")

        # Step 1: Code generate karo
        current_code = generate_flutter_code(APP_PROMPT, gen_attempt)
        
        # Step 2: Known fixes apply karo
        current_code = apply_known_fixes(current_code)

        # Step 3: Self-repair loop
        for fix_attempt in range(MAX_FIX_ATTEMPTS):
            print(f"  🔄 Fix loop {fix_attempt + 1}/{MAX_FIX_ATTEMPTS}")

            # Project banao
            create_project(current_code)

            # Errors check karo
            errors = get_errors("generated_app")

            if errors:
                print(f"  ❌ {len(errors)} analyze error(s) found:")
                for e in errors:
                    print(f"    → {e}")
                
                # AI se fix karwao
                current_code = ai_fix_errors(current_code, errors)
                continue

            # Build try karo
            print("  🔨 Building APK...")
            success, build_errors = build_apk("generated_app")

            if success:
                print(f"\n{'='*50}")
                print(f"✅ SUCCESS! APK built on generation {gen_attempt}, fix loop {fix_attempt + 1}")
                print(f"{'='*50}")
                final_success = True
                break

            if build_errors:
                print(f"  ❌ {len(build_errors)} build error(s):")
                for e in build_errors:
                    print(f"    → {e}")
                # AI se fix karwao
                current_code = ai_fix_errors(current_code, build_errors)
            else:
                print("  ❌ Build failed (unknown error)")
                break

        if final_success:
            break

        print(f"\n⚠️ Generation {gen_attempt} exhausted, trying fresh generation...\n")

    if not final_success:
        raise Exception("❌ Could not build APK after all attempts")

    print("\n🎉 APK is ready for user!")
