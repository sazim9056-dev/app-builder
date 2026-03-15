import os
import subprocess
from groq import Groq

# Environment variables se lo
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

client = Groq(api_key=GROQ_API_KEY)


def generate_flutter_code(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an expert Flutter developer. 
Generate ONLY valid Dart code for a Flutter app.
STRICT RULES:
- Start EXACTLY with: import 'package:flutter/material.dart';
- Must have: void main() => runApp(MyApp());
- Use ONLY basic Flutter Material widgets - NO external packages
- NO explanations, NO markdown, NO backticks
- Just pure Dart code only"""
            },
            {
                "role": "user",
                "content": f"Create a complete Flutter app: {prompt}"
            }
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    code = response.choices[0].message.content.strip()

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
    print("Generating Flutter code with Groq AI...")

    flutter_code = generate_flutter_code(APP_PROMPT)
    print("Code generated successfully!")

    create_flutter_project(flutter_code)
    print("Done! Ready to build APK.")
