import json
import os
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify

app = Flask(__name__)

# Ładujemy Google Credentials z ENV
try:
    credentials_info = json.loads(os.environ['CREDENTIALS_JSON'])
    credentials = Credentials.from_service_account_info(credentials_info)
    gc = gspread.authorize(credentials)
except Exception as e:
    print(f"Error loading Google credentials: {e}")
    raise e

# Otwieramy Google Sheet (upewnij się, że masz arkusz o takiej nazwie!)
try:
    sh = gc.open("StudentFeedback")  # <-- tu podmień na swoją nazwę arkusza
    worksheet = sh.sheet1
except Exception as e:
    print(f"Error opening Google Sheet: {e}")
    raise e

@app.route('/')
def home():
    return 'Auto Feedback Bot is running! 🚀'

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json()
        student_name = data['student_name']
        subject = data['subject']
        answers = data['answers']

        # Tutaj możesz dodać logikę sprawdzania odpowiedzi i generowania feedbacku
        feedback = f"Thank you, {student_name}! Good work on {subject}."

        # Dodajemy wpis do Google Sheets
        worksheet.append_row([student_name, subject, json.dumps(answers), feedback])

        return jsonify({'status': 'success', 'feedback': feedback})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
