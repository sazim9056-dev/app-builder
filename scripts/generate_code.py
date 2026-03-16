import os
import subprocess
import re
import shutil
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

client = Groq(api_key=GROQ_API_KEY)

def generate_flutter_code(prompt: str, attempt: int = 1) -> str:
    extra_instruction = ""
    if attempt == 2:
        extra_instruction = "IMPORTANT: Keep it extremely simple. Only use Text, Container, Column, Row, ElevatedButton."
    elif attempt == 3:
        extra_instruction = "CRITICAL: Make the simplest possible single screen app with basic widgets only."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a Flutter developer. Generate ONLY valid Dart code.

ABSOLUTE RULES:
1. Start with: import 'package:flutter/material.dart';
2. Use: void main() => runApp(const MyApp());
3. ONLY built-in Flutter widgets - NO external packages
4. For dark theme ALWAYS use EXACTLY:
   ThemeData(
     brightness: Brightness.dark,
     colorScheme: ColorScheme.fromSeed(
       seedColor: Colors.green,
       brightness: Brightness.dark,
     ),
     useMaterial3: true,
   )
5. When using dark theme, ALL text MUST have explicit color:
   Text('Hello', style: TextStyle(color: Colors.white))
6. ALL Container/Card backgrounds in dark theme must use dark colors like Color(0xFF1E1E1E) or Color(0xFF2D2D2D)
7. NEVER leave text color unset in dark theme - always specify color: Colors.white or Colors.white70
8. NEVER use: accentColor, primarySwatch, Transform with matrix
9. NO external packages (fl_chart, provider, http, firebase, etc.)
10. NO markdown, NO backticks, ONLY pure Dart code"""
            },
            {
                "role": "user",
                "content": f"""Create a Flutter app: {prompt}

{extra_instruction}

CRITICAL REMINDERS:
- Dark theme: ALWAYS set brightness in BOTH ThemeData AND ColorScheme
- ALL Text widgets MUST have style: TextStyle(color: Colors.white)
- ALL Icon widgets MUST have color: Colors.white
- Container backgrounds: use Color(0xFF1E1E1E) or Color(0xFF2D2D2D)
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

    # Fix 2: accentColor
    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)

    # Fix 3: primarySwatch
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,',
        code
    )

    # Fix 4: ColorScheme.fromSwatch
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )

    # Fix 5: Brightness mismatch
    if 'brightness: Brightness.dark' in code:
        code = re.sub(
            r'ColorScheme\.fromSeed\(\s*seedColor\s*:\s*(Colors\.\w+)\s*\)',
            r'ColorScheme.fromSeed(seedColor: \1, brightness: Brightness.dark)',
            code
        )

    # Fix 6: Transform matrix
    code = re.sub(r'transform\s*:\s*Transform\.[^,\n]+,?\n?', '', code)
    code = re.sub(r'transform\s*:\s*Matrix4[^,\n]+,?\n?', '', code)
    code = re.sub(r"import 'package:vector_math[^']*';\n?", '', code)

    # Fix 7: Missing colorScheme
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true, '
        )

    # Fix 8: Scaffold background black in dark theme
    # Add scaffold background color if missing
    if 'brightness: Brightness.dark' in code:
        if 'scaffoldBackgroundColor' not in code:
            code = code.replace(
                'brightness: Brightness.dark,',
                'brightness: Brightness.dark,\n      scaffoldBackgroundColor: const Color(0xFF121212),'
            )

    print("Auto-fixes applied!")
    return code


def create_flutter_project(flutter_code: str, project_name: str = "generated_app"):
    print(f"Creating Flutter project...")
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

    print("Project created!")
    return project_name


def validate_code(project_name: str) -> tuple[bool, str]:
    print("Validating code...")
    result = subprocess.run(
        ["flutter", "analyze", "--no-congratulate"],
        cwd=project_name,
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    error_count = output.lower().count('error •')
    print(f"Errors found: {error_count}")
    return error_count == 0, output


def build_apk(project_name: str) -> bool:
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
        print(f"❌ Build failed!")
        print(result.stderr[-2000:])
        return False


if __name__ == "__main__":
    print(f"🚀 AI App Builder Started")
    print(f"📝 Prompt: {APP_PROMPT}")

    max_attempts = 3
    build_success = False

    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Attempt {attempt}/{max_attempts}")

        flutter_code = generate_flutter_code(APP_PROMPT, attempt)
        flutter_code = auto_fix_code(flutter_code)

        project_name = "generated_app"
        if os.path.exists(project_name):
            shutil.rmtree(project_name)

        create_flutter_project(flutter_code, project_name)

        subprocess.run(
            ["flutter", "pub", "get"],
            cwd=project_name,
            capture_output=True, timeout=120
        )

        is_valid, _ = validate_code(project_name)
        if not is_valid:
            print(f"⚠️ Validation failed, retrying...")
            continue

        build_success = build_apk(project_name)
        if build_success:
            print(f"\n✅ SUCCESS on attempt {attempt}!")
            break
        else:
            print(f"⚠️ Build failed, retrying with simpler code...")
            if os.path.exists(project_name):
                shutil.rmtree(project_name)

    if not build_success:
        raise Exception("Could not build APK after 3 attempts")
    
    print("\n🎉 APK ready!")
