import os
import json
import openai
import gspread
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials

# Ładowanie klucza API OpenAI
openai.api_key = os.environ['OPENAI_API_KEY']

# Ładowanie poświadczeń do Google Sheets
credentials_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])

scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
gc = gspread.authorize(credentials)

# Otwieramy arkusz (upewnij się, że nazwa jest poprawna!)
sh = gc.open("Maths Calculator (Responses)")  # <-- zmień tutaj nazwę na swoją jeśli masz inną!
worksheet = sh.sheet1

# Tworzymy aplikację Flask
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Auto Feedback Bot is running!"

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json()

        if not data or 'student_name' not in data or 'answers' not in data:
            return jsonify({'error': 'Invalid input!'}), 400

        student_name = data['student_name']
        answers = data['answers']  # zakładamy, że answers to lista odpowiedzi

        # Tworzenie prompta dla OpenAI
        prompt = f"Evaluate the following student's answers and provide specific, helpful feedback. If the answer is correct, say 'Correct'. If wrong, explain why and suggest improvements.\n\nAnswers:\n"
        for i, ans in enumerate(answers, 1):
            prompt += f"{i}. {ans}\n"

        prompt += "\nWrite clear and concise feedback for each answer in English."

        # Wysyłanie do OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert English teacher helping students improve their writing and reading skills."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        feedback_text = response['choices'][0]['message']['content']

        # Zapisywanie do arkusza
        worksheet.append_row([student_name, json.dumps(answers), feedback_text])

        return jsonify({'message': 'Feedback generated successfully!', 'feedback': feedback_text}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
