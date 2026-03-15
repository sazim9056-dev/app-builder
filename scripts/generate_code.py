from google import genai
import os
import subprocess

# Environment variables se lo
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_flutter_code(prompt: str) -> str:
    system_prompt = f"""
You are an expert Flutter developer. Create a complete, working Flutter app.

User wants: {prompt}

STRICT RULES:
1. Output ONLY valid Dart code, nothing else
2. Start EXACTLY with: import 'package:flutter/material.dart';
3. Must have: void main() => runApp(MyApp());
4. Use ONLY basic Flutter Material widgets - NO external packages
5. Make it fully functional
6. NO explanations, NO markdown, NO backticks
7. Just pure Dart code only

Write the complete main.dart file now:
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=system_prompt
    )

    code = response.text.strip()

    # Clean up markdown if present
    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    # Make sure starts with import
    if not code.startswith("import"):
        idx = code.find("import 'package:flutter/material.dart'")
        if idx != -1:
            code = code[idx:]

    return code


def create_flutter_project(flutter_code: str):
    project_name = "generated_app"

    print("Creating Flutter project using flutter create...")
    result = subprocess.run(
        ["flutter", "create", "--org", "com.aibuilder", "--project-name", project_name, project_name],
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise Exception(f"Flutter create failed: {result.stderr}")

    print("Flutter project created successfully!")

    # Replace main.dart with generated code
    main_dart_path = os.path.join(project_name, "lib", "main.dart")
    with open(main_dart_path, 'w', encoding='utf-8') as f:
        f.write(flutter_code)

    print("main.dart updated!")
    print("--- Code Preview ---")
    print(flutter_code[:300])


if __name__ == "__main__":
    print(f"Prompt: {APP_PROMPT}")
    print("Generating Flutter code with Gemini...")

    flutter_code = generate_flutter_code(APP_PROMPT)
    print("Code generated!")

    create_flutter_project(flutter_code)
    print("Done! Ready to build APK.")
