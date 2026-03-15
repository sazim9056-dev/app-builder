import os
import subprocess
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
- Start EXACTLY with: import 'package:flutter/material.dart';
- Must have: void main() => runApp(const MyApp());
- Use ONLY StatelessWidget or StatefulWidget
- Use ONLY built-in Flutter Material widgets
- NO external packages, NO http, NO dio, NO provider
- NO named function expressions like: return (Function(p) {})
- NO invalid Dart syntax
- Use simple setState for state management
- NO explanations, NO markdown, NO backticks
- ONLY pure valid Dart code"""
            },
            {
                "role": "user",
                "content": f"""Create a simple Flutter app: {prompt}

Keep it simple and use only basic Flutter widgets.
Make sure all Dart syntax is 100% valid."""
            }
        ],
        temperature=0.1,
        max_tokens=3000,
    )

    code = response.choices[0].message.content.strip()

    # Clean markdown
    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    # Fix common issues
    if not code.startswith("import"):
        idx = code.find("import 'package:flutter/material.dart'")
        if idx != -1:
            code = code[idx:]

    return code


def create_flutter_project(flutter_code: str):
    project_name = "generated_app"

    print("Creating Flutter project...")
    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder", "--project-name", project_name, project_name],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise Exception(f"Flutter create failed: {result.stderr}")

    print("Project created!")

    main_dart_path = os.path.join(project_name, "lib", "main.dart")
    with open(main_dart_path, 'w', encoding='utf-8') as f:
        f.write(flutter_code)

    print("main.dart updated!")

    # Dart syntax validate karo
    print("Validating Dart syntax...")
    analyze = subprocess.run(
        ["flutter", "analyze", "lib/main.dart"],
        cwd=project_name,
        capture_output=True, text=True, timeout=60
    )

    if "error" in analyze.stdout.lower():
        print("Dart errors found, regenerating...")
        return False

    print("Syntax OK!")
    return True


if __name__ == "__main__":
    print(f"Prompt: {APP_PROMPT}")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt}/{max_attempts}...")
        print("Generating Flutter code with Groq AI...")

        flutter_code = generate_flutter_code(APP_PROMPT)
        print("Code generated!")
        print("--- Preview ---")
        print(flutter_code[:200])

        success = create_flutter_project(flutter_code)

        if success:
            print("Done! APK ready to build.")
            break
        elif attempt == max_attempts:
            print("Max attempts reached, building anyway...")
            break
        else:
            import shutil
            if os.path.exists("generated_app"):
                shutil.rmtree("generated_app")
            print("Retrying with new code...")
