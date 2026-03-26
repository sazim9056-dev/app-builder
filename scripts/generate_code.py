import os
import subprocess
import re
import shutil
import json
from groq import Groq

# ─── Environment Variables ───────────────────────────────────────────────────
GROQ_API_KEY        = os.environ.get("GROQ_API_KEY")
APP_PROMPT          = os.environ.get("APP_PROMPT", "Create a simple hello world app")
PREVIOUS_CODE       = os.environ.get("PREVIOUS_CODE", "")
CONVERSATION_HISTORY = os.environ.get("CONVERSATION_HISTORY", "")
SESSION_ID          = os.environ.get("SESSION_ID", "")

client = Groq(api_key=GROQ_API_KEY)

# ─── Icon Fixes ──────────────────────────────────────────────────────────────
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
    'Icons.tiktok'    : 'Icons.music_note',
    'Icons.reddit'    : 'Icons.forum',
    'Icons.discord'   : 'Icons.headset_mic',
    'Icons.spotify'   : 'Icons.music_note',
    'Icons.amazon'    : 'Icons.shopping_cart',
}

# ─── Banned Packages ─────────────────────────────────────────────────────────
BANNED_PACKAGES = [
    'fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
    'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
    'vector_math', 'syncfusion', 'get:', 'riverpod', 'flutter_svg',
    'cached_network_image', 'lottie', 'animations', 'rive',
    'flutter_local_notifications', 'path_provider', 'shared_preferences',
    'permission_handler', 'image_picker', 'video_player',
]

# ─── Master System Prompt ─────────────────────────────────────────────────────
MASTER_SYSTEM_PROMPT = """You are a world-class Flutter developer. You write BEAUTIFUL, COMPLETE, WORKING Flutter apps.

════════════════════════════════════════
ABSOLUTE RULES (never break these):
════════════════════════════════════════

1. IMPORTS — Always start with:
   import 'package:flutter/material.dart';
   If using math functions (pow, sqrt, sin, cos, log, pi):
   import 'dart:math' as math;
   Then use: math.pow(), math.sqrt(), math.pi — NEVER just pow()

2. ENTRY POINT — Always:
   void main() => runApp(const MyApp());

3. NO EXTERNAL PACKAGES — Only use flutter/material.dart and dart:math
   BANNED: fl_chart, http, dio, provider, bloc, firebase, google_fonts, sqflite, hive

4. ICONS — Only use Material Icons:
   VALID: Icons.home, Icons.search, Icons.add, Icons.delete, Icons.edit,
          Icons.calculate, Icons.attach_money, Icons.percent, Icons.bar_chart,
          Icons.fitness_center, Icons.check, Icons.close, Icons.star,
          Icons.favorite, Icons.share, Icons.info, Icons.settings,
          Icons.arrow_back, Icons.arrow_forward, Icons.refresh, Icons.save
   BANNED: Icons.google, Icons.facebook, Icons.twitter, Icons.apple, Icons.instagram

5. DARK THEME — Always use:
   theme: ThemeData(
     brightness: Brightness.dark,
     colorScheme: ColorScheme.fromSeed(
       seedColor: Color(0xFF6C63FF),
       brightness: Brightness.dark,
     ),
     scaffoldBackgroundColor: const Color(0xFF0F0F1A),
     useMaterial3: true,
   ),

6. TEXT COLOR — In dark theme ALL text needs explicit color:
   TextStyle(color: Colors.white)
   NEVER leave text without color in dark theme

7. NO DEPRECATED — Never use: accentColor, primarySwatch, withOpacity on
   non-existent colors. Use Color(0xFF...).withOpacity() instead.

8. STATE MANAGEMENT — Use only StatefulWidget with setState()
   No Provider, No Bloc, No Riverpod

9. OUTPUT FORMAT — Return ONLY pure Dart code
   NO markdown, NO backticks, NO explanations
   Start directly with: import 'package:flutter/material.dart';

════════════════════════════════════════
DESIGN STANDARDS (make it beautiful):
════════════════════════════════════════

- Background: const Color(0xFF0F0F1A) — deep dark
- Card color: const Color(0xFF1E1E2E) — slightly lighter
- Accent: const Color(0xFF6C63FF) — purple
- Use Container with BoxDecoration for cards (rounded, colored)
- Add subtle borders: Border.all(color: Colors.white.withOpacity(0.1))
- Use gradients where appropriate: LinearGradient
- Buttons: ElevatedButton or custom Container with gradient
- Input fields: decorated with border, hint text, proper padding
- Use SizedBox for spacing instead of Padding where simple
- Add meaningful icons to every section
- Animations: Use AnimationController for smooth transitions where useful

════════════════════════════════════════
APP STRUCTURE (always follow this):
════════════════════════════════════════

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'App Name',
      debugShowCheckedModeBanner: false,
      theme: ThemeData( /* dark theme as above */ ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget { ... }
class _HomeScreenState extends State<HomeScreen> { ... }
"""

# ─── Code Generation ──────────────────────────────────────────────────────────
def generate_flutter_code(prompt: str, previous_code: str = "", history: str = "", attempt: int = 1) -> str:
    print(f"  🤖 Generating code (attempt {attempt}/3)...")

    simplify_note = ""
    if attempt == 2:
        simplify_note = "\nNOTE: Keep it clean and simple. Avoid complex animations."
    elif attempt >= 3:
        simplify_note = "\nNOTE: Single screen only. Basic layout. No animations."

    # ── Modification mode (existing app mein changes) ──
    if previous_code and previous_code.strip():
        history_text = _build_history_text(history)

        system_msg = MASTER_SYSTEM_PROMPT + """
════════════════════════════════════════
MODIFICATION MODE:
════════════════════════════════════════
- You are modifying an EXISTING Flutter app
- KEEP all existing features intact
- Only add/change what the user requests
- Maintain the same design style and color scheme
- Return the COMPLETE updated file (not just the changed parts)
"""
        user_msg = f"""{history_text}

MODIFICATION REQUEST: {prompt}
{simplify_note}

CURRENT CODE (modify this, keep all existing features):
{previous_code}

Return the complete updated Dart code only. No explanations."""

    # ── New app mode ──
    else:
        system_msg = MASTER_SYSTEM_PROMPT + """
════════════════════════════════════════
NEW APP MODE:
════════════════════════════════════════
Create a complete, polished Flutter app based on the user's description.
Make it beautiful, functional, and impressive.
Include proper input validation, error handling, and edge cases.
"""
        user_msg = f"""Create a complete Flutter app: {prompt}
{simplify_note}

Make it beautiful with the dark theme design standards above.
Include all necessary functionality. Handle edge cases.
Return only pure Dart code starting with the import statement."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.15 if attempt == 1 else 0.05,
        max_tokens=6000,  # ⬆️ 4000 se 6000 — better apps
    )

    code = response.choices[0].message.content.strip()
    return _clean_code(code)


def _build_history_text(history: str) -> str:
    if not history:
        return ""
    try:
        history_list = json.loads(history)
        lines = ["\nCONVERSATION HISTORY (for context):"]
        for i, item in enumerate(history_list[-8:]):  # last 8 steps only
            lines.append(f"  Step {i+1} [{item['type'].upper()}]: {item['content'][:200]}")
        return "\n".join(lines)
    except Exception:
        return f"\nPREVIOUS CONTEXT: {history[:500]}"


def _clean_code(code: str) -> str:
    """Strip markdown fences and find the actual Dart code."""
    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    # Find the real start of Dart code
    for marker in ["import 'package:flutter/material.dart'", "import 'dart:math'"]:
        idx = code.find(marker)
        if idx != -1:
            return code[idx:]

    return code


# ─── Auto-Fix Known Issues ────────────────────────────────────────────────────
def apply_known_fixes(code: str) -> str:
    # Fix icons
    for wrong, correct in KNOWN_ICON_FIXES.items():
        code = code.replace(wrong, correct)

    # Remove banned packages
    for pkg in BANNED_PACKAGES:
        code = re.sub(rf"import 'package:{re.escape(pkg)}[^']*';\n?", '', code)

    # Fix deprecated: accentColor, primarySwatch
    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF)), useMaterial3: true,',
        code
    )

    # Fix ColorScheme.fromSwatch
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF))',
        code
    )

    # Fix brightness mismatch in ColorScheme
    if 'brightness: Brightness.dark' in code:
        code = re.sub(
            r'ColorScheme\.fromSeed\(\s*seedColor\s*:\s*((?:const\s+)?(?:Colors\.\w+|Color\([^)]+\)))\s*\)',
            r'ColorScheme.fromSeed(seedColor: \1, brightness: Brightness.dark)',
            code
        )

    # Fix missing useMaterial3 / colorScheme in ThemeData
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF)), useMaterial3: true, '
        )

    # Fix Transform.matrix / Matrix4
    code = re.sub(r'transform\s*:\s*Transform\.[^,\n]+,?\n?', '', code)
    code = re.sub(r'transform\s*:\s*Matrix4[^,\n]+,?\n?', '', code)
    code = re.sub(r"import 'package:vector_math[^']*';\n?", '', code)

    # ── dart:math fixes ──
    math_fns = ['pow', 'sqrt', 'sin', 'cos', 'tan', 'log', 'exp']
    needs_math = any(f'{fn}(' in code for fn in math_fns)

    if needs_math:
        if "import 'dart:math'" not in code:
            code = "import 'dart:math' as math;\n" + code

        if "as math" in code:
            for fn in math_fns:
                # Replace bare fn( with math.fn( (avoid double-prefixing)
                code = re.sub(rf'(?<!math\.){re.escape(fn)}\(', f'math.{fn}(', code)

    # Fix pi constant
    if 'pi' in code and 'math.pi' not in code and "import 'dart:math'" not in code:
        code = "import 'dart:math' as math;\n" + code
        code = re.sub(r'(?<!math\.)(?<!\w)pi(?!\w)', 'math.pi', code)

    # Fix withOpacity on Color literals (common mistake)
    code = re.sub(
        r'Color\(0x([0-9A-Fa-f]+)\)\.withOpacity\(([^)]+)\)',
        lambda m: f'Color(0x{m.group(1)}).withOpacity({m.group(2)})',
        code
    )

    # Remove duplicate imports
    lines = code.split('\n')
    seen_imports = set()
    cleaned = []
    for line in lines:
        if line.strip().startswith('import '):
            if line.strip() not in seen_imports:
                seen_imports.add(line.strip())
                cleaned.append(line)
        else:
            cleaned.append(line)
    code = '\n'.join(cleaned)

    return code


# ─── AI Error Fixer ───────────────────────────────────────────────────────────
def ai_fix_errors(code: str, errors: list) -> str:
    print(f"  🔧 AI fixing {len(errors)} error(s)...")

    # Fast path: only math errors → fix without AI
    math_errors = [e for e in errors if any(
        kw in e for kw in ["'pow' isn't", "'sqrt' isn't", "'sin' isn't",
                           "'cos' isn't", "'log' isn't", "'pi' isn't"]
    )]
    if math_errors and len(math_errors) == len(errors):
        print("  ⚡ Fast fix: dart:math")
        if "import 'dart:math'" not in code:
            code = "import 'dart:math' as math;\n" + code
        for fn in ['pow', 'sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'pi']:
            code = re.sub(rf'(?<!math\.){re.escape(fn)}\b', f'math.{fn}', code)
        return code

    # Fast path: banned package errors
    pkg_errors = [e for e in errors if 'package:' in e and 'not found' in e.lower()]
    if pkg_errors and len(pkg_errors) == len(errors):
        print("  ⚡ Fast fix: removing bad packages")
        return apply_known_fixes(code)

    # Full AI fix
    error_text = "\n".join(f"  {i+1}. {e}" for i, e in enumerate(errors[:10]))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are fixing Flutter/Dart compile errors.

RULES:
- Return ONLY the complete fixed Dart code
- NO markdown, NO backticks, NO explanations  
- Keep all existing functionality
- Fix ONLY the reported errors

COMMON FIXES:
- 'pow' isn't defined → add "import 'dart:math' as math;" and use math.pow()
- Package not found → remove that import entirely
- Undefined name 'X' → replace with a valid Flutter equivalent
- Type mismatch → add proper cast (.toDouble(), .toInt(), .toString())
- Missing const → add or remove const as needed"""
            },
            {
                "role": "user",
                "content": f"Fix these errors:\n{error_text}\n\nCode:\n{code}\n\nReturn fixed code only."
            }
        ],
        temperature=0.05,
        max_tokens=6000,
    )

    fixed = response.choices[0].message.content.strip()
    fixed = _clean_code(fixed)
    return apply_known_fixes(fixed)


# ─── Flutter Project Setup ────────────────────────────────────────────────────
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

    with open(os.path.join(project_name, "lib", "main.dart"), 'w', encoding='utf-8') as f:
        f.write(code)

    subprocess.run(
        ["flutter", "pub", "get"],
        cwd=project_name, capture_output=True, timeout=120
    )


def get_errors(project_name: str) -> list:
    result = subprocess.run(
        ["flutter", "analyze", "--no-congratulate"],
        cwd=project_name, capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    errors = [line.strip() for line in output.split('\n') if 'error •' in line.lower()]
    return errors


def build_apk(project_name: str) -> tuple:
    result = subprocess.run(
        ["flutter", "build", "apk", "--debug", "--no-shrink"],
        cwd=project_name, capture_output=True, text=True, timeout=600
    )
    if result.returncode == 0:
        return True, []
    build_errors = [
        line.strip() for line in result.stderr.split('\n')
        if 'error:' in line.lower() and ('lib/' in line or 'dart:' in line)
    ]
    # Also check stdout for errors
    if not build_errors:
        build_errors = [
            line.strip() for line in result.stdout.split('\n')
            if 'error:' in line.lower()
        ][:5]
    return False, build_errors


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("🚀  AI APP BUILDER — SELF-HEALING ENGINE  v2.0")
    print("=" * 55)
    print(f"📝 Prompt  : {APP_PROMPT[:100]}")
    print(f"🔑 Session : {SESSION_ID or 'N/A'}")

    if PREVIOUS_CODE:
        print(f"🔄 Mode    : Modifying existing app ({len(PREVIOUS_CODE)} chars)")
    else:
        print("✨ Mode    : Creating new app")

    if CONVERSATION_HISTORY:
        try:
            h = json.loads(CONVERSATION_HISTORY)
            print(f"📚 History : {len(h)} previous steps")
        except Exception:
            pass

    MAX_GENERATIONS = 3
    MAX_FIX_LOOPS   = 6   # ⬆️ 5 → 6 fix attempts
    final_success   = False
    current_code    = ""

    for gen in range(1, MAX_GENERATIONS + 1):
        print(f"\n{'━'*20} GENERATION {gen}/{MAX_GENERATIONS} {'━'*20}")

        current_code = generate_flutter_code(
            APP_PROMPT, PREVIOUS_CODE, CONVERSATION_HISTORY, gen
        )
        current_code = apply_known_fixes(current_code)

        consecutive_same_errors = 0
        last_errors = []

        for fix in range(MAX_FIX_LOOPS):
            print(f"\n  🔄 Attempt {fix + 1}/{MAX_FIX_LOOPS}")
            create_project(current_code)
            errors = get_errors("generated_app")

            if errors:
                print(f"  ❌ {len(errors)} analyze error(s):")
                for e in errors[:5]:
                    print(f"     → {e}")

                # Detect infinite loop (same errors repeating)
                if errors == last_errors:
                    consecutive_same_errors += 1
                    if consecutive_same_errors >= 2:
                        print("  ⚠️  Same errors repeating — forcing regeneration")
                        break
                else:
                    consecutive_same_errors = 0
                last_errors = errors

                current_code = ai_fix_errors(current_code, errors)
                current_code = apply_known_fixes(current_code)
                continue

            print("  ✅ No analyze errors — building APK...")
            success, build_errors = build_apk("generated_app")

            if success:
                print(f"\n  🎉 SUCCESS! (Generation {gen}, Attempt {fix + 1})")
                final_success = True
                break
            else:
                print(f"  ❌ Build failed — {len(build_errors)} error(s):")
                for e in build_errors[:5]:
                    print(f"     → {e}")
                if build_errors:
                    current_code = ai_fix_errors(current_code, build_errors)
                    current_code = apply_known_fixes(current_code)
                else:
                    print("  ⚠️  Unknown build failure")
                    break

        if final_success:
            break
        if gen < MAX_GENERATIONS:
            print(f"\n  ⚠️  Generation {gen} exhausted → fresh attempt...\n")

    if not final_success:
        raise Exception("❌ Could not build APK after all attempts")

    # Save final code for artifact upload
    with open("final_code.dart", "w", encoding='utf-8') as f:
        f.write(current_code)

    print("\n" + "=" * 55)
    print("🎉  APK READY!")
    print("=" * 55)
