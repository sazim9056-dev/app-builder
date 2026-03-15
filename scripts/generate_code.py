import os
import subprocess
import re
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

client = Groq(api_key=GROQ_API_KEY)


def generate_flutter_code(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a Flutter developer. Generate ONLY simple, basic Flutter code.

ABSOLUTE RULES - NO EXCEPTIONS:
1. Start with: import 'package:flutter/material.dart';
2. Use: void main() => runApp(const MyApp());
3. ONLY use these widgets: Scaffold, AppBar, Column, Row, Container, Text, ElevatedButton, TextButton, ListView, ListTile, Card, Icon, TextField, Padding, SizedBox, Expanded, Center, SingleChildScrollView, BottomNavigationBar, FloatingActionButton, AlertDialog, showDialog, CircleAvatar, Divider, Wrap, Stack, Positioned, Navigator, MaterialPageRoute, TabBar, TabBarView, DefaultTabController, Checkbox, Switch, Radio, Slider, DropdownButton, PopupMenuButton, IconButton, CircularProgressIndicator
4. ThemeData MUST use: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true)
5. NEVER use Transform widget with transform parameter
6. NEVER use Matrix4
7. NEVER use any external packages
8. NEVER use fl_chart, charts, provider, http, dio, firebase
9. For rotating: use Transform.rotate() as a WIDGET wrapping child, NOT as parameter
10. Keep code SIMPLE - no complex animations or transforms
11. NO markdown, NO backticks, ONLY pure Dart code"""
            },
            {
                "role": "user",
                "content": f"Create a simple Flutter app: {prompt}\n\nKEEP IT SIMPLE. Use only basic Material widgets. No transforms, no animations, no external packages."
            }
        ],
        temperature=0.1,
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

    # ============ AUTO FIX COMMON ERRORS ============

    # Fix accentColor
    code = re.sub(r'\baccentColor\s*:.*?,?\n?', '', code)

    # Fix primarySwatch
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        'colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,',
        code
    )

    # Fix ColorScheme.fromSwatch
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )

    # Fix transform: Transform.rotate(...) → remove entire transform line
    code = re.sub(r'transform\s*:\s*Transform\.[^,\n]+,?\n?', '', code)

    # Fix transform: Matrix4... → remove
    code = re.sub(r'transform\s*:\s*Matrix4[^,\n]+,?\n?', '', code)

    # Remove Matrix4 imports if any
    code = re.sub(r"import 'package:vector_math[^']*';\n?", '', code)

    # Fix missing colorScheme in ThemeData
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true, '
        )

    # Remove any non-flutter package imports
    bad_packages = ['fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
                    'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
                    'vector_math', 'syncfusion', 'get:', 'riverpod']
    for pkg in bad_packages:
        code = re.sub(rf"import 'package:{pkg}[^']*';\n?", '', code)

    return code


def create_flutter_project(flutter_code: str):
    project_name = "generated_app"

    print("Creating Flutter project...")
    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder",
         "--project-name", project_name, project_name],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise Exception(f"Flutter create failed: {result.stderr}")

    print("Project created!")

    main_dart_path = os.path.join(project_name, "lib", "main.dart")
    with open(main_dart_path, 'w', encoding='utf-8') as f:
        f.write(flutter_code)

    print("main.dart updated!")
    print("--- Preview ---")
    print(flutter_code[:300])
    return True


if __name__ == "__main__":
    print(f"Prompt: {APP_PROMPT}")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt}/{max_attempts}...")
        print("Generating Flutter code with Groq AI...")

        flutter_code = generate_flutter_code(APP_PROMPT)
        print("Code generated!")

        success = create_flutter_project(flutter_code)

        if success:
            print("Done! Ready to build APK.")
            break
        elif attempt == max_attempts:
            print("Building with last generated code...")
        else:
            import shutil
            if os.path.exists("generated_app"):
                shutil.rmtree("generated_app")
            print("Retrying...")
