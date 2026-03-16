import os
import subprocess
import re
import shutil
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

client = Groq(api_key=GROQ_API_KEY)

# ============================================
# LAYER 1: SMART CODE GENERATION
# ============================================
def generate_flutter_code(prompt: str, attempt: int = 1) -> str:
    
    extra_instruction = ""
    if attempt == 2:
        extra_instruction = "IMPORTANT: Keep it extremely simple. Only use Text, Container, Column, Row, ElevatedButton widgets."
    elif attempt == 3:
        extra_instruction = "CRITICAL: Make the simplest possible app. Just one screen with basic widgets only."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a Flutter developer. Generate ONLY valid Dart code.

ABSOLUTE RULES - NO EXCEPTIONS:
1. Start EXACTLY with: import 'package:flutter/material.dart';
2. Must have: void main() => runApp(const MyApp());
3. ONLY use built-in Flutter Material widgets
4. NO external packages (fl_chart, provider, http, firebase, etc.)
5. For dark theme ALWAYS use:
   ThemeData(
     brightness: Brightness.dark,
     colorScheme: ColorScheme.fromSeed(
       seedColor: Colors.blue,
       brightness: Brightness.dark,
     ),
     useMaterial3: true,
   )
6. For light theme use:
   ThemeData(
     colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
     useMaterial3: true,
   )
7. NEVER use: accentColor, primarySwatch, Transform with matrix
8. NEVER use fl_chart, charts, syncfusion for graphs
9. For graphs/charts: use Container + Row with colored boxes
10. NO markdown, NO backticks, ONLY pure Dart code"""
            },
            {
                "role": "user",
                "content": f"""Create a Flutter app: {prompt}

{extra_instruction}

REMEMBER: 
- Only built-in Flutter widgets
- Dark theme: set brightness in BOTH ThemeData AND ColorScheme
- No external packages at all"""
            }
        ],
        temperature=0.1 if attempt == 1 else 0.05,
        max_tokens=4000,
    )

    code = response.choices[0].message.content.strip()

    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    if not code.startswith("import"):
        idx = code.find("import 'package:flutter/material.dart'")
        if idx != -1:
            code = code[idx:]

    return code


# ============================================
# LAYER 2: AUTO FIX ALL KNOWN ERRORS
# ============================================
def auto_fix_code(code: str) -> str:
    print("Applying auto-fixes...")

    # Fix 1: Remove bad package imports
    bad_packages = [
        'fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
        'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
        'vector_math', 'syncfusion', 'get:', 'riverpod', 'intl',
        'shared_preferences', 'path_provider', 'image_picker'
    ]
    for pkg in bad_packages:
        code = re.sub(rf"import 'package:{pkg}[^']*';\n?", '', code)

    # Fix 2: accentColor (deprecated)
    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)

    # Fix 3: primarySwatch (deprecated)
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,',
        code
    )

    # Fix 4: ColorScheme.fromSwatch (old API)
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )

    # Fix 5: Brightness mismatch - MOST IMPORTANT
    if 'brightness: Brightness.dark' in code:
        code = re.sub(
            r'ColorScheme\.fromSeed\(\s*seedColor\s*:\s*(Colors\.\w+)\s*\)',
            r'ColorScheme.fromSeed(seedColor: \1, brightness: Brightness.dark)',
            code
        )

    # Fix 6: Transform matrix errors
    code = re.sub(r'transform\s*:\s*Transform\.[^,\n]+,?\n?', '', code)
    code = re.sub(r'transform\s*:\s*Matrix4[^,\n]+,?\n?', '', code)
    code = re.sub(r"import 'package:vector_math[^']*';\n?", '', code)

    # Fix 7: Missing colorScheme in ThemeData
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true, '
        )

    # Fix 8: secondary color in ColorScheme (old API)
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*secondary[^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )

    # Fix 9: Null safety issues - required parameters
    code = re.sub(r'(?<!\bconst\s)(?<!\bnew\s)\bText\(\)', "Text('')", code)

    print("Auto-fixes applied!")
    return code


# ============================================
# LAYER 3: VALIDATE + BUILD + TEST
# ============================================
def create_flutter_project(flutter_code: str, project_name: str = "generated_app"):
    print(f"Creating Flutter project: {project_name}")
    
    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder",
         "--project-name", project_name, project_name],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise Exception(f"Flutter create failed: {result.stderr}")

    main_dart_path = os.path.join(project_name, "lib", "main.dart")
    with open(main_dart_path, 'w', encoding='utf-8') as f:
        f.write(flutter_code)

    print("Project created and code injected!")
    return project_name


def validate_code(project_name: str) -> tuple[bool, str]:
    """Flutter analyze se code validate karo"""
    print("Validating code with flutter analyze...")
    
    result = subprocess.run(
        ["flutter", "analyze", "--no-congratulate"],
        cwd=project_name,
        capture_output=True, text=True, timeout=120
    )
    
    output = result.stdout + result.stderr
    
    # Count errors
    error_count = output.lower().count('error •')
    warning_count = output.lower().count('warning •')
    
    print(f"Analyze result: {error_count} errors, {warning_count} warnings")
    
    if error_count == 0:
        print("✅ Code validation passed!")
        return True, output
    else:
        print(f"❌ Code has {error_count} errors")
        return False, output


def build_apk(project_name: str) -> bool:
    """APK build karo"""
    print("Building APK...")
    
    result = subprocess.run(
        ["flutter", "build", "apk", "--debug"],
        cwd=project_name,
        capture_output=True, text=True, timeout=600
    )
    
    if result.returncode == 0:
        print("✅ APK build successful!")
        return True
    else:
        print(f"❌ APK build failed!")
        print(result.stderr[-2000:])  # Last 2000 chars of error
        return False


# ============================================
# MAIN: SELF-HEALING PIPELINE
# ============================================
if __name__ == "__main__":
    print(f"🚀 Starting AI App Builder")
    print(f"📝 Prompt: {APP_PROMPT}")
    print("="*50)

    max_attempts = 3
    build_success = False

    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Attempt {attempt}/{max_attempts}")
        print("-"*30)

        # Step 1: Generate code
        print("🤖 Generating Flutter code...")
        flutter_code = generate_flutter_code(APP_PROMPT, attempt)
        
        # Step 2: Auto fix
        flutter_code = auto_fix_code(flutter_code)

        # Step 3: Create project
        project_name = "generated_app"
        if os.path.exists(project_name):
            shutil.rmtree(project_name)
        
        create_flutter_project(flutter_code, project_name)

        # Step 4: Flutter pub get
        print("📦 Getting dependencies...")
        subprocess.run(
            ["flutter", "pub", "get"],
            cwd=project_name,
            capture_output=True, timeout=120
        )

        # Step 5: Validate
        is_valid, analyze_output = validate_code(project_name)
        
        if not is_valid:
            print(f"⚠️ Attempt {attempt} validation failed, retrying...")
            continue

        # Step 6: Build APK
        build_success = build_apk(project_name)
        
        if build_success:
            print(f"\n✅ SUCCESS on attempt {attempt}!")
            break
        else:
            print(f"⚠️ Build failed on attempt {attempt}, retrying with simpler code...")
            if os.path.exists(project_name):
                shutil.rmtree(project_name)

    if build_success:
        print("\n🎉 APK ready for user!")
    else:
        print("\n❌ All attempts failed!")
        raise Exception("Could not build APK after 3 attempts")
