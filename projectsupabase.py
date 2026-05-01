from flask import Flask, render_template, request, jsonify
import json, re, random, ssl, urllib.request, urllib.error
import os
app = Flask(__name__)
# ── SSL FIX ──────────────────────────────────────────────
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# ── CONFIG ───────────────────────────────────────────────
GROK_API_KEY = os.getenv("API_KEY")
GROK_URL     = "https://api.groq.com/openai/v1/chat/completions"

# ── SUPABASE CONFIG ───────────────────────────────────────
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_SECRET = os.getenv("SECRET_KEY")

# ── CURRICULUM ────────────────────────────────────────────
CURRICULUM = [
    {
        "name": "Hello World", "level": 1, "topic": "Variables & Print",
        "subgoals": [
            {"pos": [0,0], "hint": "Create a variable called name and store a name in it", "statement": 'name = "Alice"'},
            {"pos": [0,1], "hint": "Print a greeting using that variable", "statement": 'print("Hello", name)'},
        ],
        "goal_pos": [0,3], "full_code": 'name = "Alice"\nprint("Hello", name)\n',
        "traps": [[1,0],[2,0]],
        "trap_messages": {"1,0": "No functions yet!", "2,0": "No loop needed."},
    },
    {
        "name": "Add Two Numbers", "level": 1, "topic": "Variables & Print",
        "subgoals": [
            {"pos": [0,0], "hint": "Store first number in a",  "statement": "a = 5"},
            {"pos": [0,1], "hint": "Store second number in b", "statement": "b = 3"},
            {"pos": [1,1], "hint": "Add them into result",     "statement": "result = a + b"},
            {"pos": [1,2], "hint": "Print the result",         "statement": "print(result)"},
        ],
        "goal_pos": [0,3], "full_code": "a = 5\nb = 3\nresult = a + b\nprint(result)\n",
        "traps": [[2,0],[3,1]],
        "trap_messages": {"2,0": "No loop needed!", "3,1": "No function needed."},
    },
    {
        "name": "Check Positive", "level": 2, "topic": "If / Else",
        "subgoals": [
            {"pos": [0,0], "hint": "Store a number in n",       "statement": "n = 7"},
            {"pos": [0,1], "hint": "Check if n > 0",            "statement": "if n > 0:"},
            {"pos": [1,1], "hint": "Print Positive (indented)", "statement": '    print("Positive")'},
            {"pos": [1,2], "hint": "Add else",                  "statement": "else:"},
            {"pos": [2,2], "hint": "Print Not positive",        "statement": '    print("Not positive")'},
        ],
        "goal_pos": [0,3], "full_code": 'n = 7\nif n > 0:\n    print("Positive")\nelse:\n    print("Not positive")\n',
        "traps": [[3,0],[2,1]],
        "trap_messages": {"3,0": "Just if/else!", "2,1": "elif is for multiple conditions."},
    },
    {
        "name": "Even or Odd", "level": 2, "topic": "If / Else",
        "subgoals": [
            {"pos": [0,0], "hint": "Get number from user",  "statement": "n = int(input())"},
            {"pos": [0,1], "hint": "Check divisible by 2",  "statement": "if n % 2 == 0:"},
            {"pos": [1,1], "hint": "Print Even",            "statement": '    print("Even")'},
            {"pos": [1,2], "hint": "Print Odd in else",     "statement": '    print("Odd")'},
        ],
        "goal_pos": [0,3], "full_code": 'n = int(input())\nif n % 2 == 0:\n    print("Even")\nelse:\n    print("Odd")\n',
        "traps": [[2,0],[3,2]],
        "trap_messages": {"2,0": "No loop!", "3,2": "Use % for remainder."},
    },
    {
        "name": "Count to 5", "level": 3, "topic": "For Loops",
        "subgoals": [
            {"pos": [0,0], "hint": "Start for loop 1 to 5",    "statement": "for i in range(1, 6):"},
            {"pos": [0,1], "hint": "Print i (4 spaces indent)", "statement": "    print(i)"},
        ],
        "goal_pos": [0,3], "full_code": "for i in range(1, 6):\n    print(i)\n",
        "traps": [[1,0],[2,1]],
        "trap_messages": {"1,0": "Use range(1,6)!", "2,1": "for is simpler here."},
    },
    {
        "name": "Sum 1 to N", "level": 3, "topic": "For Loops",
        "subgoals": [
            {"pos": [0,0], "hint": "Get n from user",       "statement": "n = int(input())"},
            {"pos": [0,1], "hint": "Start total at 0",      "statement": "total = 0"},
            {"pos": [1,1], "hint": "Loop i from 1 to n",    "statement": "for i in range(1, n+1):"},
            {"pos": [1,2], "hint": "Add i to total",        "statement": "    total += i"},
            {"pos": [2,2], "hint": "Print total",           "statement": "print(total)"},
        ],
        "goal_pos": [0,3], "full_code": "n = int(input())\ntotal = 0\nfor i in range(1, n+1):\n    total += i\nprint(total)\n",
        "traps": [[2,0],[3,2]],
        "trap_messages": {"2,0": "total+1 not i!", "3,2": "Use range(1, n+1)."},
    },
    {
        "name": "Countdown", "level": 4, "topic": "While Loops",
        "subgoals": [
            {"pos": [0,0], "hint": "Set count to 5",                   "statement": "count = 5"},
            {"pos": [0,1], "hint": "While count > 0",                  "statement": "while count > 0:"},
            {"pos": [1,1], "hint": "Print count",                      "statement": "    print(count)"},
            {"pos": [1,2], "hint": "Decrease count (avoid inf loop!)", "statement": "    count -= 1"},
        ],
        "goal_pos": [0,3], "full_code": "count = 5\nwhile count > 0:\n    print(count)\n    count -= 1\n",
        "traps": [[2,0],[3,1]],
        "trap_messages": {"2,0": "Missing -= causes infinite loop!", "3,1": "+= goes up forever!"},
    },
    {
        "name": "Greet Function", "level": 5, "topic": "Functions",
        "subgoals": [
            {"pos": [0,0], "hint": "Define greet(name)",        "statement": "def greet(name):"},
            {"pos": [0,1], "hint": "Print greeting (indented)", "statement": '    print("Hello", name)'},
            {"pos": [1,1], "hint": "Call the function",         "statement": 'greet("Alice")'},
        ],
        "goal_pos": [0,3], "full_code": 'def greet(name):\n    print("Hello", name)\n\ngreet("Alice")\n',
        "traps": [[2,0],[3,2]],
        "trap_messages": {"2,0": "Define before calling!", "3,2": "Don't forget the colon."},
    },
    {
        "name": "Factorial", "level": 5, "topic": "Functions",
        "subgoals": [
            {"pos": [0,0], "hint": "Get n from user",       "statement": "n = int(input())"},
            {"pos": [0,1], "hint": "Start result at 1",     "statement": "result = 1"},
            {"pos": [1,1], "hint": "Loop 1 to n",           "statement": "for i in range(1, n+1):"},
            {"pos": [1,2], "hint": "Multiply result by i",  "statement": "    result *= i"},
            {"pos": [2,2], "hint": "Print result",          "statement": "print(result)"},
        ],
        "goal_pos": [0,3], "full_code": "n = int(input())\nresult = 1\nfor i in range(1, n+1):\n    result *= i\nprint(result)\n",
        "traps": [[2,1],[3,2],[1,0]],
        "trap_messages": {"2,1": "for is cleaner.", "3,2": "Loops better here.", "1,0": "Init result=1 first!"},
    },
]

# ── SUPABASE HELPER ───────────────────────────────────────
def supabase_insert(table, data):
    url  = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req  = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type":  "application/json",
            "apikey":        SUPABASE_SECRET,
            "Authorization": f"Bearer {SUPABASE_SECRET}",
            "Prefer":        "return=minimal"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10, context=ssl_context) as r:
        return r.status

# ── GROQ API ──────────────────────────────────────────────
def call_groq(prompt):
    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 512,
    }).encode()
    req = urllib.request.Request(
        GROK_URL, data=body,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {GROK_API_KEY}",
            "User-Agent":    "Mozilla/5.0",
            "Accept":        "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60, context=ssl_context) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def build_generation_prompt(topic):
    return f"""You are an expert Python tutor for absolute beginners.
Create a 4x4 RL gridworld problem for teaching: "{topic}"

Return ONLY valid JSON. No markdown, no code fences, no extra text.

{{
  "problem_name": "Short name",
  "level": 3,
  "topic": "{topic}",
  "subgoals": [
    {{"pos": [0,0], "hint": "Beginner-friendly hint", "statement": "short_code"}},
    {{"pos": [0,1], "hint": "Beginner-friendly hint", "statement": "short_code"}},
    {{"pos": [1,1], "hint": "Beginner-friendly hint", "statement": "short_code"}},
    {{"pos": [1,2], "hint": "Beginner-friendly hint", "statement": "short_code"}}
  ],
  "goal_pos": [0,3],
  "full_code": "# complete code\\nprint('done')\\n",
  "traps": [[2,1],[3,2]],
  "trap_messages": {{"2,1": "educational message", "3,2": "educational message"}}
}}

RULES:
- full_code must use \\n for newlines.
- Keep each statement under 25 characters.
- All positions must be unique and in range 0-3.
- Return ONLY the JSON object."""

def parse_generated_json(raw, topic):
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    s = raw.find("{"); e = raw.rfind("}") + 1
    if s == -1 or e == 0:
        raise ValueError("No JSON found")
    raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw[s:e])
    data = json.loads(raw)
    subgoals = [{"pos": list(sg["pos"]), "hint": sg["hint"], "statement": sg["statement"]}
                for sg in data["subgoals"]]
    return {
        "name":      data["problem_name"],
        "level":     data.get("level", 3),
        "topic":     data.get("topic", topic),
        "subgoals":  subgoals,
        "goal_pos":  list(data["goal_pos"]),
        "full_code": data["full_code"].replace("\\n", "\n").replace("\\t", "\t"),
        "traps":     [list(p) for p in data.get("traps", [])],
        "trap_messages": {
            ",".join(map(str, k)) if isinstance(k, list) else k: v
            for k, v in data.get("trap_messages", {}).items()
        },
        "source": "groq",
    }

def randomise_positions(problem):
    import copy
    p    = copy.deepcopy(problem)
    goal = tuple(p["goal_pos"])
    pool = [[r, c] for r in range(4) for c in range(4) if [r, c] != list(goal)]
    random.shuffle(pool)
    for i, sg in enumerate(p["subgoals"]):
        sg["pos"] = pool[i]
    tc = len(p.get("traps", []))
    p["traps"] = pool[len(p["subgoals"]):len(p["subgoals"]) + tc]
    return p

# ── ROUTES ────────────────────────────────────────────────
@app.route("/")
def index():
    problems = [{"name": p["name"], "level": p["level"], "topic": p["topic"]} for p in CURRICULUM]
    return render_template("index.html", problems=problems)

@app.route("/api/problem/<name>")
def get_problem(name):
    for p in CURRICULUM:
        if p["name"] == name:
            rp = randomise_positions(p)
            rp["source"] = "builtin"
            return jsonify(rp)
    return jsonify({"error": "Not found"}), 404

@app.route("/api/generate", methods=["POST"])
def generate_problem():
    data  = request.json
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Topic required"}), 400
    try:
        prompt  = build_generation_prompt(topic)
        raw     = call_groq(prompt)
        problem = parse_generated_json(raw, topic)
        problem["source"] = "groq"
        rp = randomise_positions(problem)
        return jsonify(rp)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    entry = request.json
    try:
        supabase_insert("feedback", entry)
        return jsonify({"ok": True})
    except Exception as e:
        # Fallback to local JSON if Supabase fails
        try:
            try:
                with open("feedback_log.json") as f:
                    log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                log = []
            log.append(entry)
            with open("feedback_log.json", "w") as f:
                json.dump(log, f, indent=2)
            return jsonify({"ok": True, "warning": "Saved locally"})
        except Exception as e2:
            return jsonify({"error": str(e2)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
