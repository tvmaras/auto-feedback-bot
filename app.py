import json
import os
import openai
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify

# Konfiguracja OpenAI
openai.api_key = os.environ['OPENAI_API_KEY']

# Ładowanie Google Sheets credentials
credentials_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])

# WAŻNE: Dodanie poprawnego scope
scopes = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)

# Autoryzacja do Google Sheets
gc = gspread.authorize(credentials)

# Otwieranie arkusza
sh = gc.open("StudentFeedback")  # <-- Zamień na nazwę swojego arkusza jeśli masz inną!
worksheet = sh.sheet1

# Konfiguracja Flask
app = Flask(__name__)

# Endpoint do testu działania
@app.route('/')
def home():
    return "Auto Feedback Bot is live!"

# Endpoint do oceny odpowiedzi
@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.json
        student_name = data['student_name']
        answers = data['answers']  # Lista odpowiedzi ucznia

        all_feedback = []
        correct_answers = 0

        for i, answer in enumerate(answers, 1):
            prompt = f"Evaluate the student's answer:\nQuestion {i}: {answer}\nGive a brief and clear feedback."
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            feedback_text = response['choices'][0]['message']['content'].strip()
            all_feedback.append((answer, feedback_text))

            if "correct" in feedback_text.lower() or "good" in feedback_text.lower():
                correct_answers += 1

        total_questions = len(answers)
        score_percentage = round((correct_answers / total_questions) * 100, 2)

        # Przygotuj dane do zapisania w arkuszu
        row = [student_name, f"{score_percentage}%"] + [f"A{i}: {ans} | Feedback: {fb}" for i, (ans, fb) in enumerate(all_feedback, 1)]
        worksheet.append_row(row)

        return jsonify({"message": "Feedback generated and saved.", "score": score_percentage})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
