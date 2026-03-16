import os
import subprocess
import re
import shutil
import json
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")
PREVIOUS_CODE = os.environ.get("PREVIOUS_CODE", "")
CONVERSATION_HISTORY = os.environ.get("CONVERSATION_HISTORY", "")  # Pura history

client = Groq(api_key=GROQ_API_KEY)

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


def generate_flutter_code(prompt: str, previous_code: str = "", history: str = "", attempt: int = 1) -> str:
    print(f"  Generating code (attempt {attempt})...")

    extra = ""
    if attempt == 2:
        extra = "SIMPLIFY: Use only basic widgets."
    elif attempt >= 3:
        extra = "MAKE IT VERY SIMPLE: Single screen only."

    # Agar previous code + history hai toh poora context bhejo
    if previous_code and previous_code.strip():
        
        # History parse karo
        history_text = ""
        if history:
            try:
                history_list = json.loads(history)
                history_text = "\n\nCOMPLETE CONVERSATION HISTORY:\n"
                for i, item in enumerate(history_list):
                    history_text += f"Step {i+1} - {item['type'].upper()}: {item['content']}\n"
            except:
                history_text = f"\n\nPREVIOUS CONTEXT: {history}"

        system_msg = """You are an expert Flutter developer. You are modifying an existing Flutter app.

CRITICAL RULES:
1. You have the FULL conversation history showing what was built before
2. You must KEEP all existing features from the current code
3. You must ONLY ADD or MODIFY what the user requested in the latest change
4. Think of it like git - you're building ON TOP of the existing app
5. Return ONLY complete valid Dart code
6. Start with: import 'package:flutter/material.dart';
7. ONLY built-in Flutter widgets - NO external packages
8. VALID Icons only - NEVER use Icons.google, Icons.facebook etc.
9. ALL Text in dark theme MUST have color: TextStyle(color: Colors.white)
10. NO markdown, NO backticks"""

        user_msg = f"""Here is the complete history of this app:
{history_text}

LATEST CHANGE REQUESTED: {prompt}

CURRENT CODE (keep all existing features, only apply the latest change):
{previous_code}

{extra}

IMPORTANT: 
- Keep ALL existing screens and features
- Only modify/add what was requested in "LATEST CHANGE REQUESTED"
- Return the complete updated Dart code"""

    else:
        # Fresh app - sirf original prompt
        system_msg = """You are an expert Flutter developer. Generate ONLY valid Dart code.

RULES:
1. Start with: import 'package:flutter/material.dart';
2. Use: void main() => runApp(const MyApp());
3. ONLY built-in Flutter widgets - NO external packages
4. Dark theme:
   theme: ThemeData(
     brightness: Brightness.dark,
     colorScheme: ColorScheme.fromSeed(
       seedColor: Colors.blue,
       brightness: Brightness.dark,
     ),
     useMaterial3: true,
   ),
5. VALID Icons: Icons.home, Icons.search, Icons.person, Icons.settings,
   Icons.email, Icons.lock, Icons.visibility, Icons.visibility_off,
   Icons.add, Icons.delete, Icons.edit, Icons.check, Icons.close,
   Icons.arrow_back, Icons.menu, Icons.star, Icons.favorite,
   Icons.language, Icons.phone, Icons.camera_alt, Icons.notifications,
   Icons.fitness_center, Icons.directions_run, Icons.local_fire_department,
   Icons.water_drop, Icons.bar_chart, Icons.restaurant, Icons.shopping_cart,
   Icons.calculate, Icons.attach_money, Icons.percent
6. NEVER use: Icons.google, Icons.facebook, Icons.twitter, Icons.apple
7. ALL Text in dark theme MUST have color: TextStyle(color: Colors.white)
8. NEVER use: accentColor, primarySwatch, fl_chart, any external package
9. NO markdown, NO backticks - ONLY pure Dart code"""

        user_msg = f"Create Flutter app: {prompt}\n\n{extra}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
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


def apply_known_fixes(code: str) -> str:
    for wrong, correct in KNOWN_FIXES.items():
        code = code.replace(wrong, correct)

    bad_packages = [
        'fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
        'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
        'vector_math', 'syncfusion', 'get:', 'riverpod', 'intl',
        'shared_preferences', 'path_provider', 'image_picker',
        'flutter_svg', 'cached_network_image', 'lottie'
    ]
    for pkg in bad_packages:
        code = re.sub(rf"import 'package:{pkg}[^']*';\n?", '', code)

    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,',
        code
    )
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )

    if 'brightness: Brightness.dark' in code:
        code = re.sub(
            r'ColorScheme\.fromSeed\(\s*seedColor\s*:\s*(Colors\.\w+)\s*\)',
            r'ColorScheme.fromSeed(seedColor: \1, brightness: Brightness.dark)',
            code
        )

    code = re.sub(r'transform\s*:\s*Transform\.[^,\n]+,?\n?', '', code)
    code = re.sub(r'transform\s*:\s*Matrix4[^,\n]+,?\n?', '', code)
    code = re.sub(r"import 'package:vector_math[^']*';\n?", '', code)

    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true, '
        )

    return code


def ai_fix_errors(code: str, errors: list) -> str:
    print(f"  Fixing {len(errors)} error(s)...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Fix Flutter Dart errors. Return ONLY complete fixed code. No explanations, no markdown."
            },
            {
                "role": "user",
                "content": f"Fix errors:\n{chr(10).join(errors)}\n\nCode:\n{code}\n\nReturn fixed code only."
            }
        ],
        temperature=0.05,
        max_tokens=4000,
    )

    fixed = response.choices[0].message.content.strip()

    if "```dart" in fixed:
        fixed = fixed.split("```dart")[1].split("```")[0].strip()
    elif "```" in fixed:
        fixed = fixed.split("```")[1].split("```")[0].strip()

    if not fixed.startswith("import"):
        idx = fixed.find("import 'package:flutter/material.dart'")
        if idx != -1:
            fixed = fixed[idx:]

    return apply_known_fixes(fixed)


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

    subprocess.run(["flutter", "pub", "get"], cwd=project_name,
                   capture_output=True, timeout=120)


def get_errors(project_name: str) -> list:
    result = subprocess.run(
        ["flutter", "analyze", "--no-congratulate"],
        cwd=project_name, capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    return [line.strip() for line in output.split('\n') if 'error •' in line.lower()]


def build_apk(project_name: str) -> tuple:
    result = subprocess.run(
        ["flutter", "build", "apk", "--debug"],
        cwd=project_name, capture_output=True, text=True, timeout=600
    )
    if result.returncode == 0:
        return True, []
    build_errors = [line.strip() for line in result.stderr.split('\n')
                    if 'error:' in line.lower() and 'lib/' in line]
    return False, build_errors


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 SELF-HEALING AI APP BUILDER")
    print("=" * 50)
    print(f"📝 Prompt: {APP_PROMPT[:80]}...")
    
    if PREVIOUS_CODE:
        print("🔄 Modifying existing app (with full history)...")
    if CONVERSATION_HISTORY:
        try:
            h = json.loads(CONVERSATION_HISTORY)
            print(f"📚 History: {len(h)} previous steps remembered")
        except:
            pass

    MAX_GEN = 3
    MAX_FIX = 5
    final_success = False

    for gen in range(1, MAX_GEN + 1):
        print(f"\n━━━ GENERATION {gen}/{MAX_GEN} ━━━")

        current_code = generate_flutter_code(APP_PROMPT, PREVIOUS_CODE, CONVERSATION_HISTORY, gen)
        current_code = apply_known_fixes(current_code)

        for fix in range(MAX_FIX):
            print(f"  🔄 Fix loop {fix + 1}/{MAX_FIX}")
            create_project(current_code)
            errors = get_errors("generated_app")

            if errors:
                print(f"  ❌ {len(errors)} error(s):")
                for e in errors:
                    print(f"    → {e}")
                current_code = ai_fix_errors(current_code, errors)
                continue

            print("  🔨 Building APK...")
            success, build_errors = build_apk("generated_app")

            if success:
                print(f"\n✅ SUCCESS! Gen {gen}, Fix {fix + 1}")
                final_success = True
                break

            if build_errors:
                print(f"  ❌ Build errors:")
                for e in build_errors:
                    print(f"    → {e}")
                current_code = ai_fix_errors(current_code, build_errors)
            else:
                break

        if final_success:
            break
        print(f"\n⚠️ Gen {gen} exhausted, fresh generation...\n")

    if not final_success:
        raise Exception("Could not build APK after all attempts")

    print("\n🎉 APK ready!")
