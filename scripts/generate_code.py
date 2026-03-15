import google.generativeai as genai
import os
import shutil

# Environment variables se lo
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
APP_PROMPT = os.environ.get("APP_PROMPT", "Create a simple hello world app")

genai.configure(api_key=GEMINI_API_KEY)


def generate_flutter_code(prompt: str) -> str:
    model = genai.GenerativeModel('gemini-pro')

    system_prompt = f"""
You are an expert Flutter developer. Create a complete, working Flutter app.

User wants: {prompt}

STRICT RULES:
1. Output ONLY valid Dart code, nothing else
2. Start with: import 'package:flutter/material.dart';
3. Must have void main() function
4. Use Material Design widgets
5. Make it fully functional and visually good
6. NO explanations, NO markdown, NO backticks
7. Just pure Dart code only

Write the complete main.dart file:
"""

    response = model.generate_content(system_prompt)
    code = response.text.strip()

    # Clean up any markdown if present
    if "```dart" in code:
        code = code.split("```dart")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    return code


def create_flutter_project(flutter_code: str):
    project_name = "generated_app"

    # Template Flutter project structure banao
    os.makedirs(f"{project_name}/lib", exist_ok=True)
    os.makedirs(f"{project_name}/android/app/src/main", exist_ok=True)

    # pubspec.yaml
    pubspec = """name: generated_app
description: AI Generated Flutter App
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
"""
    with open(f"{project_name}/pubspec.yaml", "w") as f:
        f.write(pubspec)

    # main.dart with generated code
    with open(f"{project_name}/lib/main.dart", "w") as f:
        f.write(flutter_code)

    # AndroidManifest.xml
    manifest = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application
        android:label="Generated App"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
"""
    os.makedirs(f"{project_name}/android/app/src/main", exist_ok=True)
    with open(f"{project_name}/android/app/src/main/AndroidManifest.xml", "w") as f:
        f.write(manifest)

    print(f"Flutter project created: {project_name}")


if __name__ == "__main__":
    print(f"Generating app for prompt: {APP_PROMPT}")

    flutter_code = generate_flutter_code(APP_PROMPT)
    print("Flutter code generated successfully!")
    print("--- Generated Code Preview ---")
    print(flutter_code[:200] + "...")

    create_flutter_project(flutter_code)
    print("Project structure created!")
