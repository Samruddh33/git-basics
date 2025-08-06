from flask import Flask, request, redirect, session, render_template_string, url_for
import os
import random
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)  # ✅ CORRECTED
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ====================== HTML Templates ======================

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>StudyLoop - Upload</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h2>📚 StudyLoop</h2>
        <form method="POST" enctype="multipart/form-data">
            <label>Select your study material (PDF):</label><br><br>
            <input type="file" name="studyfile" required><br><br>
            <button type="submit">Start Quiz</button>
        </form>
    </div>
</body>
</html>
"""

QUIZ_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>StudyLoop - Quiz</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h2>Quiz Time!</h2>
        <form method="POST">
            {% for q in quiz %}
                <p><b>Q{{ loop.index }}:</b> {{ q.question }}</p>
                <input type="text" name="answer_{{ q.id }}" required><br><br>
            {% endfor %}
            <button type="submit">Submit Quiz</button>
        </form>
    </div>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>StudyLoop - Result</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h2>Your Score: {{ score }}/{{ total }}</h2>
        <h3>📝 Revision Content:</h3>
        {% if revision %}
            <ul>
            {% for r in revision %}
                <li>{{ r }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>Great job! No revision needed.</p>
        {% endif %}
        <br><br>
        <a href="/">Upload Another File</a>
    </div>
</body>
</html>
"""

STYLE_CSS = """
body {
  font-family: sans-serif;
  background: #f0f8ff;
  text-align: center;
  padding-top: 50px;
}

.container {
  width: 60%;
  margin: auto;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  border-radius: 10px;
}

input[type="text"], input[type="file"] {
  padding: 10px;
  width: 80%;
}

button {
  padding: 10px 20px;
  background: #2e8b57;
  color: white;
  border: none;
  border-radius: 5px;
}
"""

# ====================== Helper Functions ======================

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def generate_quiz(content):
    lines = [line.strip() for line in content.split('.') if len(line.split()) > 5]
    questions = random.sample(lines, min(5, len(lines)))
    quiz = []
    for i, line in enumerate(questions):
        words = line.split()
        if len(words) > 6:
            answer = words[5]
            words[5] = "_"
            quiz.append({
                "id": i,
                "question": " ".join(words),
                "answer": answer
            })
    return quiz

# ====================== Routes ======================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["studyfile"]
        if file and file.filename.endswith(".pdf"):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            text = extract_text_from_pdf(filepath)
            quiz = generate_quiz(text)
            session["quiz"] = quiz
            session["original_text"] = text
            return redirect(url_for("quiz"))
    return render_template_string(INDEX_HTML, css=STYLE_CSS)

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    quiz = session.get("quiz", [])
    if request.method == "POST":
        score = 0
        wrong = []
        for q in quiz:
            user_ans = request.form.get(f"answer_{q['id']}", "").strip().lower()
            correct = q["answer"].strip().lower()
            if user_ans == correct:
                score += 1
            else:
                wrong.append(q)
        revision = [q["question"].replace("_", q["answer"]) for q in wrong]
        session["score"] = score
        session["revision"] = revision
        return redirect(url_for("result"))
    return render_template_string(QUIZ_HTML, quiz=quiz, css=STYLE_CSS)

@app.route("/result")
def result():
    score = session.get("score", 0)
    revision = session.get("revision", [])
    total = len(session.get("quiz", []))
    return render_template_string(RESULT_HTML, score=score, total=total, revision=revision, css=STYLE_CSS)

# ====================== Run ======================

if __name__ == "__main__":  # ✅ CORRECTED
    app.run(debug=True)
