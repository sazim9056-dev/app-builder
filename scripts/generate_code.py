import os
import subprocess
import re
import shutil
import json
from groq import Groq

GROQ_API_KEY        = os.environ.get("GROQ_API_KEY")
APP_PROMPT          = os.environ.get("APP_PROMPT", "Create a simple hello world app")
PREVIOUS_CODE       = os.environ.get("PREVIOUS_CODE", "")
CONVERSATION_HISTORY = os.environ.get("CONVERSATION_HISTORY", "")
SESSION_ID          = os.environ.get("SESSION_ID", "")

client = Groq(api_key=GROQ_API_KEY)

KNOWN_ICON_FIXES = {
    'Icons.google'    : 'Icons.language',
    'Icons.facebook'  : 'Icons.thumb_up',
    'Icons.twitter'   : 'Icons.tag',
    'Icons.instagram' : 'Icons.camera_alt',
    'Icons.apple'     : 'Icons.phone_iphone',
    'Icons.whatsapp'  : 'Icons.chat',
    'Icons.youtube'   : 'Icons.play_circle',
    'Icons.github'    : 'Icons.code',
    'Icons.microsoft' : 'Icons.window',
    'Icons.linkedin'  : 'Icons.work',
}

BANNED_PACKAGES = [
    'fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
    'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
    'vector_math', 'syncfusion', 'get:', 'riverpod', 'flutter_svg',
    'cached_network_image', 'lottie',
]

SYSTEM_PROMPT = """You are a world-class Flutter developer. Generate BEAUTIFUL, COMPLETE, WORKING Flutter apps.

ABSOLUTE RULES:
1. Always start with: import 'package:flutter/material.dart';
2. For math: import 'dart:math' as math; then use math.pow(), math.sqrt()
3. Entry point: void main() => runApp(const MyApp());
4. NO EXTERNAL PACKAGES — Only flutter/material.dart and dart:math
   NEVER use: fl_chart, http, dio, provider, firebase, google_fonts, sqflite
5. VALID ICONS ONLY: Icons.home, Icons.search, Icons.add, Icons.delete,
   Icons.calculate, Icons.attach_money, Icons.check, Icons.star, Icons.settings
   NEVER: Icons.google, Icons.facebook, Icons.twitter, Icons.apple
6. DARK THEME:
   theme: ThemeData(
     brightness: Brightness.dark,
     colorScheme: ColorScheme.fromSeed(
       seedColor: const Color(0xFF6C63FF),
       brightness: Brightness.dark,
     ),
     scaffoldBackgroundColor: const Color(0xFF0F0F1A),
     useMaterial3: true,
   ),
7. ALL Text needs: TextStyle(color: Colors.white)
8. NEVER use: accentColor, primarySwatch
9. OUTPUT: ONLY pure Dart code. No markdown, no backticks.
   Start with: import 'package:flutter/material.dart';

DESIGN:
- Background: const Color(0xFF0F0F1A)
- Cards: const Color(0xFF1E1E2E) with BorderRadius.circular(12)
- Accent: const Color(0xFF6C63FF)
- Handle all edge cases (empty input, divide by zero, etc.)
"""


def generate_flutter_code(prompt, previous_code="", history="", attempt=1):
    print(f"  Generating code (attempt {attempt}/3)...")

    simplify = ""
    if attempt == 2:
        simplify = "\nKEEP IT SIMPLE: Avoid complex animations."
    elif attempt >= 3:
        simplify = "\nVERY SIMPLE: Single screen, basic layout only."

    if previous_code and previous_code.strip():
        history_text = _build_history(history)
        system = SYSTEM_PROMPT + "\nMODIFICATION MODE: Keep ALL existing features. Only change what user requests."
        user = f"""{history_text}

MODIFICATION REQUEST: {prompt}
{simplify}

CURRENT CODE:
{previous_code}

Return complete updated Dart code only."""
    else:
        system = SYSTEM_PROMPT + "\nNEW APP MODE: Create a complete, polished, functional app."
        user = f"""Create a complete Flutter app: {prompt}
{simplify}

Make it beautiful with dark theme. Handle all edge cases.
Return only pure Dart code starting with the import statement."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.15 if attempt == 1 else 0.05,
        max_tokens=6000,
    )

    code = response.choices[0].message.content.strip()
    return _clean_code(code)


def _build_history(history):
    if not history:
        return ""
    try:
        items = json.loads(history)
        lines = ["\nCONVERSATION HISTORY:"]
        for i, item in enumerate(items[-8:]):
            lines.append(f"  Step {i+1} [{item['type'].upper()}]: {item['content'][:200]}")
        return "\n".join(lines)
    except Exception:
        return ""


def _clean_code(code):
    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    for marker in ["import 'package:flutter/material.dart'", "import 'dart:math'"]:
        idx = code.find(marker)
        if idx != -1:
            return code[idx:]
    return code


def apply_known_fixes(code):
    for wrong, correct in KNOWN_ICON_FIXES.items():
        code = code.replace(wrong, correct)
    for pkg in BANNED_PACKAGES:
        code = re.sub(rf"import 'package:{re.escape(pkg)}[^']*';\n?", '', code)
    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF)), useMaterial3: true,',
        code
    )
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF))',
        code
    )
    if 'brightness: Brightness.dark' in code:
        code = re.sub(
            r'ColorScheme\.fromSeed\(\s*seedColor\s*:\s*((?:const\s+)?(?:Colors\.\w+|Color\([^)]+\)))\s*\)',
            r'ColorScheme.fromSeed(seedColor: \1, brightness: Brightness.dark)',
            code
        )
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF)), useMaterial3: true, '
        )
    math_fns = ['pow', 'sqrt', 'sin', 'cos', 'tan', 'log', 'exp']
    if any(f'{fn}(' in code for fn in math_fns):
        if "import 'dart:math'" not in code:
            code = "import 'dart:math' as math;\n" + code
        if "as math" in code:
            for fn in math_fns:
                code = re.sub(rf'(?<!math\.){re.escape(fn)}\(', f'math.{fn}(', code)
    lines = code.split('\n')
    seen = set()
    result = []
    for line in lines:
        if line.strip().startswith('import '):
            if line.strip() not in seen:
                seen.add(line.strip())
                result.append(line)
        else:
            result.append(line)
    return '\n'.join(result)


def ai_fix_errors(code, errors):
    print(f"  Fixing {len(errors)} error(s)...")
    math_errors = [e for e in errors if any(
        kw in e for kw in ["'pow' isn't", "'sqrt' isn't", "'sin' isn't"]
    )]
    if math_errors and len(math_errors) == len(errors):
        if "import 'dart:math'" not in code:
            code = "import 'dart:math' as math;\n" + code
        for fn in ['pow', 'sqrt', 'sin', 'cos', 'tan', 'log']:
            code = re.sub(rf'(?<!math\.){re.escape(fn)}\(', f'math.{fn}(', code)
        return code

    error_text = "\n".join(f"  {i+1}. {e}" for i, e in enumerate(errors[:10]))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Fix Flutter/Dart errors. Return ONLY complete fixed Dart code. No markdown, no backticks."},
            {"role": "user",   "content": f"Fix these errors:\n{error_text}\n\nCode:\n{code}\n\nReturn fixed code only."}
        ],
        temperature=0.05,
        max_tokens=6000,
    )
    fixed = response.choices[0].message.content.strip()
    return apply_known_fixes(_clean_code(fixed))


def create_project(code, project_name="generated_app"):
    if os.path.exists(project_name):
        shutil.rmtree(project_name)
    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder",
         "--project-name", project_name, project_name],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise Exception(f"Flutter create failed: {result.stderr}")
    with open(os.path.join(project_name, "lib", "main.dart"), 'w', encoding='utf-8') as f:
        f.write(code)
    subprocess.run(["flutter", "pub", "get"], cwd=project_name, capture_output=True, timeout=120)


def get_errors(project_name):
    result = subprocess.run(
        ["flutter", "analyze", "--no-congratulate"],
        cwd=project_name, capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    return [line.strip() for line in output.split('\n') if 'error •' in line.lower()]


def build_apk(project_name):
    result = subprocess.run(
        ["flutter", "build", "apk", "--release"],
        cwd=project_name, capture_output=True, text=True, timeout=600
    )
    if result.returncode == 0:
        return True, []
    errors = [
        line.strip() for line in result.stderr.split('\n')
        if 'error:' in line.lower() and 'lib/' in line
    ]
    return False, errors


if __name__ == "__main__":
    print("=" * 55)
    print("AI APP BUILDER — GROQ POWERED")
    print("=" * 55)
    print(f"Prompt  : {APP_PROMPT[:100]}")
    print(f"Session : {SESSION_ID or 'N/A'}")
    print(f"Mode    : {'Modifying' if PREVIOUS_CODE else 'New app'}")

    MAX_GEN = 3
    MAX_FIX = 6
    final_success = False
    current_code = ""

    for gen in range(1, MAX_GEN + 1):
        print(f"\n{'='*20} GENERATION {gen}/{MAX_GEN} {'='*20}")
        current_code = generate_flutter_code(APP_PROMPT, PREVIOUS_CODE, CONVERSATION_HISTORY, gen)
        current_code = apply_known_fixes(current_code)

        last_errors = []
        same_count = 0

        for fix in range(MAX_FIX):
            print(f"  Attempt {fix + 1}/{MAX_FIX}")
            create_project(current_code)
            errors = get_errors("generated_app")

            if errors:
                print(f"  {len(errors)} error(s) found")
                if errors == last_errors:
                    same_count += 1
                    if same_count >= 2:
                        print("  Same errors — regenerating")
                        break
                else:
                    same_count = 0
                last_errors = errors
                current_code = apply_known_fixes(ai_fix_errors(current_code, errors))
                continue

            print("  No errors — building APK...")
            success, build_errors = build_apk("generated_app")

            if success:
                print(f"\n  SUCCESS! Gen {gen}, Fix {fix + 1}")
                final_success = True
                break
            elif build_errors:
                current_code = apply_known_fixes(ai_fix_errors(current_code, build_errors))
            else:
                break

        if final_success:
            break

    if not final_success:
        raise Exception("Could not build APK after all attempts")

    with open("final_code.dart", "w", encoding='utf-8') as f:
        f.write(current_code)

    print("\n" + "=" * 55)
    print("APK READY!")
    print("=" * 55)
