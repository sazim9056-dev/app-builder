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
                "content": """You are an expert Flutter developer. Generate ONLY valid Dart code.

STRICT RULES:
1. Start EXACTLY with: import 'package:flutter/material.dart';
2. Must have: void main() => runApp(const MyApp());
3. Use ONLY built-in Flutter Material widgets - NO external packages
4. NEVER use: fl_chart, charts_flutter, provider, bloc, http, dio, sqflite, firebase, google_fonts
5. For charts: use Container + Row + Column with colored boxes only
6. For ThemeData, use EXACTLY this pattern:
   ThemeData(
     colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
     useMaterial3: true,
   )
7. NEVER use: accentColor, primarySwatch, ColorScheme.fromSwatch with secondary
8. NO explanations, NO markdown, NO backticks
9. Just pure valid Dart code only"""
            },
            {
                "role": "user",
                "content": f"Create a complete Flutter app: {prompt}\n\nIMPORTANT: Use ONLY built-in Flutter widgets. NO external packages."
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

    # Auto fix common errors
    # Fix accentColor
    code = re.sub(r'accentColor\s*:.*?,', '', code)
    
    # Fix primarySwatch
    code = re.sub(
        r'primarySwatch\s*:\s*Colors\.\w+,?',
        "colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,",
        code
    )
    
    # Fix ColorScheme.fromSwatch with secondary (invalid)
    code = re.sub(
        r'ColorScheme\.fromSwatch\([^)]*secondary[^)]*\)',
        'ColorScheme.fromSeed(seedColor: Colors.blue)',
        code
    )
    
    # Fix ThemeData with just primarySwatch gone - ensure colorScheme exists
    if 'ThemeData(' in code and 'colorScheme' not in code:
        code = code.replace(
            'ThemeData(',
            'ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true,'
        )

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
