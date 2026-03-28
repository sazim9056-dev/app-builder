import os
import subprocess
import re
import shutil
import json
from groq import Groq

GROQ_API_KEY         = os.environ.get("GROQ_API_KEY")
APP_PROMPT           = os.environ.get("APP_PROMPT", "Create a simple hello world app")
PREVIOUS_CODE        = os.environ.get("PREVIOUS_CODE", "")
CONVERSATION_HISTORY = os.environ.get("CONVERSATION_HISTORY", "")
SESSION_ID           = os.environ.get("SESSION_ID", "")

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
    'Icons.tiktok'    : 'Icons.music_note',
    'Icons.spotify'   : 'Icons.music_note',
}

BANNED_PACKAGES = [
    'fl_chart', 'charts_flutter', 'provider', 'bloc', 'http',
    'dio', 'sqflite', 'hive', 'firebase', 'google_fonts',
    'vector_math', 'syncfusion', 'get:', 'riverpod', 'flutter_svg',
    'cached_network_image', 'lottie', 'animations', 'rive',
]

# ═══════════════════════════════════════════════════════════════
# MASTER SYSTEM PROMPT — v5.0 ULTRA
# ═══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are a world-class Flutter developer. Generate PRODUCTION-QUALITY, COMPLETE, WORKING Flutter apps — just like apps on the Play Store.

════════════════════════════════════════════════════
ABSOLUTE RULES (never break these):
════════════════════════════════════════════════════

1. IMPORTS:
   import 'package:flutter/material.dart';
   import 'dart:convert';       // for JSON storage
   import 'dart:math' as math;  // for math functions → use math.pow(), math.sqrt()

2. ENTRY POINT:
   void main() => runApp(const MyApp());

3. NO EXTERNAL PACKAGES:
   ONLY allowed: flutter/material.dart, dart:math, dart:convert, dart:async
   NEVER use: fl_chart, http, dio, provider, bloc, firebase, google_fonts,
              sqflite, hive, shared_preferences, riverpod, flutter_svg

4. LOCAL DATA STORAGE — Use this exact pattern (no external packages):
   import 'dart:convert';
   // Store data as static variable (in-memory, persists during session)
   static List<Map<String, dynamic>> _data = [];
   // For JSON: jsonEncode(_data) and jsonDecode(jsonString)

5. ICONS — Only Material Icons:
   VALID: Icons.home, Icons.search, Icons.add, Icons.delete, Icons.edit,
          Icons.calculate, Icons.attach_money, Icons.percent, Icons.bar_chart,
          Icons.check, Icons.close, Icons.star, Icons.settings, Icons.refresh,
          Icons.arrow_back, Icons.arrow_forward, Icons.favorite, Icons.share,
          Icons.person, Icons.group, Icons.camera_alt, Icons.image,
          Icons.notifications, Icons.shopping_cart, Icons.payment,
          Icons.fitness_center, Icons.restaurant, Icons.directions_car,
          Icons.flight, Icons.hotel, Icons.local_hospital, Icons.school,
          Icons.work, Icons.book, Icons.music_note, Icons.movie,
          Icons.sports_soccer, Icons.games, Icons.chat, Icons.email
   NEVER: Icons.google, Icons.facebook, Icons.twitter, Icons.apple, Icons.instagram

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

7. ALL Text in dark theme needs explicit color:
   style: const TextStyle(color: Colors.white)
   style: const TextStyle(color: Colors.white70)
   style: const TextStyle(color: Colors.white54)

8. NEVER use: accentColor, primarySwatch, ColorScheme.fromSwatch

9. OUTPUT: ONLY pure Dart code. NO markdown, NO backticks, NO explanations.
   Start directly with: import 'package:flutter/material.dart';

════════════════════════════════════════════════════
DESIGN STANDARDS — Play Store Quality:
════════════════════════════════════════════════════

COLORS:
  Background:  const Color(0xFF0F0F1A)
  Card:        const Color(0xFF1E1E2E)
  Accent:      const Color(0xFF6C63FF)
  Success:     const Color(0xFF00D68F)
  Warning:     const Color(0xFFFFAA00)
  Danger:      const Color(0xFFFF4D4D)

CARDS:
  Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: const Color(0xFF1E1E2E),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withOpacity(0.08)),
    ),
    child: ...
  )

BUTTONS:
  ElevatedButton(
    style: ElevatedButton.styleFrom(
      backgroundColor: const Color(0xFF6C63FF),
      foregroundColor: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  )

INPUT FIELDS:
  TextField(
    style: const TextStyle(color: Colors.white),
    decoration: InputDecoration(
      filled: true,
      fillColor: const Color(0xFF1E1E2E),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.white.withOpacity(0.1)),
      ),
      labelStyle: const TextStyle(color: Colors.white54),
    ),
  )

APPBAR:
  AppBar(
    backgroundColor: const Color(0xFF16213E),
    elevation: 0,
    title: const Text('App Name', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
    iconTheme: const IconThemeData(color: Colors.white),
  )

════════════════════════════════════════════════════
MULTI-SCREEN NAVIGATION — Always use this pattern:
════════════════════════════════════════════════════

Navigator.push(context, MaterialPageRoute(builder: (_) => const NextScreen()));
Navigator.pop(context);

// For bottom navigation:
class HomeScreen extends StatefulWidget { ... }
class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final _screens = [Screen1(), Screen2(), Screen3()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        backgroundColor: const Color(0xFF1E1E2E),
        selectedItemColor: const Color(0xFF6C63FF),
        unselectedItemColor: Colors.white38,
        onTap: (i) => setState(() => _currentIndex = i),
        items: const [...],
      ),
    );
  }
}

════════════════════════════════════════════════════
LOCAL DATA STORAGE — In-memory pattern:
════════════════════════════════════════════════════

// Use static lists to persist data across screens (no external package needed)
class DataStore {
  static List<Map<String, dynamic>> items = [];
  static double totalBalance = 0.0;

  static void addItem(Map<String, dynamic> item) {
    items.add(item);
  }

  static void removeItem(int index) {
    items.removeAt(index);
  }
}

════════════════════════════════════════════════════
CHARTS — Draw with Canvas (no external package):
════════════════════════════════════════════════════

// Bar Chart using CustomPaint:
class BarChart extends StatelessWidget {
  final List<double> values;
  final List<String> labels;
  const BarChart({required this.values, required this.labels, super.key});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size(double.infinity, 200),
      painter: _BarChartPainter(values: values, labels: labels),
    );
  }
}

class _BarChartPainter extends CustomPainter {
  final List<double> values;
  final List<String> labels;
  _BarChartPainter({required this.values, required this.labels});

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;
    final maxVal = values.reduce((a, b) => a > b ? a : b);
    final barWidth = size.width / (values.length * 2);
    final paint = Paint()..color = const Color(0xFF6C63FF);
    final textPainter = TextPainter(textDirection: TextDirection.ltr);

    for (int i = 0; i < values.length; i++) {
      final x = i * barWidth * 2 + barWidth / 2;
      final barH = maxVal > 0 ? (values[i] / maxVal) * (size.height - 30) : 0.0;
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(x, size.height - 30 - barH, barWidth, barH),
          const Radius.circular(4),
        ),
        paint,
      );
      // Label
      textPainter.text = TextSpan(
        text: labels[i],
        style: const TextStyle(color: Colors.white54, fontSize: 10),
      );
      textPainter.layout();
      textPainter.paint(canvas, Offset(x + barWidth / 2 - textPainter.width / 2, size.height - 20));
    }
  }

  @override
  bool shouldRepaint(_BarChartPainter old) => true;
}

// Line Chart using CustomPaint:
class LineChart extends StatelessWidget {
  final List<double> values;
  const LineChart({required this.values, super.key});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size(double.infinity, 150),
      painter: _LineChartPainter(values: values),
    );
  }
}

class _LineChartPainter extends CustomPainter {
  final List<double> values;
  _LineChartPainter({required this.values});

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final maxVal = values.reduce((a, b) => a > b ? a : b);
    final minVal = values.reduce((a, b) => a < b ? a : b);
    final range = maxVal - minVal == 0 ? 1.0 : maxVal - minVal;
    final path = Path();
    final paint = Paint()
      ..color = const Color(0xFF6C63FF)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke;

    for (int i = 0; i < values.length; i++) {
      final x = i * size.width / (values.length - 1);
      final y = size.height - ((values[i] - minVal) / range) * size.height;
      if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
    }
    canvas.drawPath(path, paint);

    // Dots
    final dotPaint = Paint()..color = const Color(0xFF6C63FF);
    for (int i = 0; i < values.length; i++) {
      final x = i * size.width / (values.length - 1);
      final y = size.height - ((values[i] - minVal) / range) * size.height;
      canvas.drawCircle(Offset(x, y), 4, dotPaint);
    }
  }

  @override
  bool shouldRepaint(_LineChartPainter old) => true;
}

// Pie Chart using CustomPaint:
class PieChart extends StatelessWidget {
  final List<double> values;
  final List<Color> colors;
  final List<String> labels;
  const PieChart({required this.values, required this.colors, required this.labels, super.key});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size(200, 200),
      painter: _PieChartPainter(values: values, colors: colors),
    );
  }
}

class _PieChartPainter extends CustomPainter {
  final List<double> values;
  final List<Color> colors;
  _PieChartPainter({required this.values, required this.colors});

  @override
  void paint(Canvas canvas, Size size) {
    final total = values.fold(0.0, (a, b) => a + b);
    if (total == 0) return;
    double startAngle = -math.pi / 2;
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 10;

    for (int i = 0; i < values.length; i++) {
      final sweepAngle = (values[i] / total) * 2 * math.pi;
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle, sweepAngle, true,
        Paint()..color = colors[i % colors.length],
      );
      startAngle += sweepAngle;
    }
  }

  @override
  bool shouldRepaint(_PieChartPainter old) => true;
}

════════════════════════════════════════════════════
ANIMATIONS — Use these patterns:
════════════════════════════════════════════════════

// Fade animation:
class _MyScreenState extends State<MyScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _fadeAnim = Tween<double>(begin: 0.0, end: 1.0).animate(_controller);
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

// Use: FadeTransition(opacity: _fadeAnim, child: ...)
// Slide: SlideTransition(position: _slideAnim, child: ...)
// Scale: ScaleTransition(scale: _scaleAnim, child: ...)

// Simple AnimatedContainer for smooth UI:
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF1E1E2E),
)

════════════════════════════════════════════════════
APP CATEGORIES — How to build each type:
════════════════════════════════════════════════════

CALCULATOR APPS (EMI, BMI, SIP, Tax, Age, Unit Converter):
- Single or 2 screens
- TextFields for input with number keyboard
- Results shown in styled cards
- Use math.pow() for compound calculations

PRODUCTIVITY APPS (Todo, Notes, Habit Tracker, Planner):
- Multiple screens with Navigator
- DataStore class with static List for storage
- CRUD operations (add, edit, delete, toggle)
- ListView.builder for lists
- Swipe to delete with Dismissible

FINANCE APPS (Expense Tracker, Budget, Invoice):
- Bottom navigation (Summary / Add / History)
- DataStore for transactions
- Bar/Pie charts with CustomPaint
- Category filtering
- Total calculations

HEALTH & FITNESS (Water Tracker, Step Counter, Workout):
- Progress indicators (CircularProgressIndicator, LinearProgressIndicator)
- Daily goals and streaks
- AnimatedContainer for progress

GAMES (Quiz, Memory, Puzzle, Snake):
- Game state management with setState
- Timer with Timer.periodic from dart:async
- Score tracking
- Animations for game events

UTILITY APPS (Password Gen, QR Info, Flashcards, Dictionary):
- Clean single or multi-screen layout
- List/Grid views
- Search functionality
- Copy to clipboard with Clipboard.setData

════════════════════════════════════════════════════
ALWAYS INCLUDE:
════════════════════════════════════════════════════
- Input validation (show SnackBar for errors)
- Empty state UI (show message when list is empty)
- Loading states where needed
- Proper error handling
- Edge cases (divide by zero, empty fields, etc.)
- const constructors everywhere possible
- Responsive layout (use MediaQuery or Expanded/Flexible)
"""


def generate_flutter_code(prompt, previous_code="", history="", attempt=1):
    print(f"  Generating code (attempt {attempt}/3)...")

    simplify = ""
    if attempt == 2:
        simplify = "\nSIMPLIFY: Reduce animations, keep core features only."
    elif attempt >= 3:
        simplify = "\nMINIMAL: Single screen, no animations, basic layout."

    if previous_code and previous_code.strip():
        history_text = _build_history(history)
        system = SYSTEM_PROMPT + "\nMODIFICATION MODE: Keep ALL existing features. Only add/change what user requests. Return complete file."
        user = f"""{history_text}

MODIFICATION REQUEST: {prompt}
{simplify}

CURRENT CODE:
{previous_code}

Return COMPLETE updated Dart code only. No explanations."""

    else:
        system = SYSTEM_PROMPT + "\nNEW APP MODE: Create a complete, polished, Play Store quality app."
        user = f"""Create a complete Flutter app: {prompt}
{simplify}

Requirements:
- Beautiful dark theme UI
- All features fully working
- Handle all edge cases
- Use multi-screen if needed
- Add charts if data visualization needed
- Smooth animations

Return ONLY pure Dart code starting with import statement."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.15 if attempt == 1 else 0.05,
        max_tokens=8000,
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
    for marker in ["import 'package:flutter/material.dart'", "import 'dart:math'", "import 'dart:convert'"]:
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

    # dart:math fixes
    math_fns = ['pow', 'sqrt', 'sin', 'cos', 'tan', 'log', 'exp']
    if any(f'{fn}(' in code for fn in math_fns):
        if "import 'dart:math'" not in code:
            code = "import 'dart:math' as math;\n" + code
        if "as math" in code:
            for fn in math_fns:
                code = re.sub(rf'(?<!math\.){re.escape(fn)}\(', f'math.{fn}(', code)

    # Remove duplicate imports
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
        kw in e for kw in ["'pow' isn't", "'sqrt' isn't", "'sin' isn't", "'cos' isn't", "'pi' isn't"]
    )]
    if math_errors and len(math_errors) == len(errors):
        if "import 'dart:math'" not in code:
            code = "import 'dart:math' as math;\n" + code
        for fn in ['pow', 'sqrt', 'sin', 'cos', 'tan', 'log', 'pi']:
            code = re.sub(rf'(?<!math\.){re.escape(fn)}\b', f'math.{fn}', code)
        return code

    error_text = "\n".join(f"  {i+1}. {e}" for i, e in enumerate(errors[:10]))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Fix Flutter/Dart compile errors. Return ONLY complete fixed Dart code.
NO markdown, NO backticks, NO explanations.
Keep ALL existing functionality — only fix the reported errors.
Common fixes:
- 'pow' not defined → add import 'dart:math' as math; and use math.pow()
- Package not found → remove that import
- Type error → add proper cast
- Missing const → add or remove as needed"""
            },
            {
                "role": "user",
                "content": f"Fix errors:\n{error_text}\n\nCode:\n{code}\n\nReturn fixed code only."
            }
        ],
        temperature=0.05,
        max_tokens=8000,
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
    if not errors:
        errors = [l.strip() for l in result.stdout.split('\n') if 'error:' in l.lower()][:5]
    return False, errors


if __name__ == "__main__":
    print("=" * 55)
    print("AI APP BUILDER v5.0 — PLAY STORE QUALITY")
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
                        print("  Same errors repeating — regenerating")
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
