import os
import json
import openai
import gspread
import io
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from fpdf import FPDF

# Ładowanie kluczy API
openai.api_key = os.environ['OPENAI_API_KEY']

# Google Credentials + Scope do Drive
credentials_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)

# Google Drive klient
drive_service = build('drive', 'v3', credentials=credentials)

# Google Sheets klient
gc = gspread.authorize(credentials)
sh = gc.open("Maths Calculator (Responses)")  # <-- zmień jeśli masz inną nazwę arkusza
worksheet = sh.sheet1

# ID folderu na Drive, gdzie chcesz wrzucać PDFy
FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")  # Ustaw to w Render jako sekret!

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Auto Feedback Bot is running!"

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json()

        if not data or 'student_name' not in data or 'answers' not in data or 'form_name' not in data:
            return jsonify({'error': 'Invalid input!'}), 400

        student_name = data['student_name']
        form_name = data['form_name']
        answers = data['answers']

        # Tworzenie prompta
        prompt = f"Evaluate the following student's answers and provide specific, helpful feedback. If the answer is correct, say 'Correct'. If wrong, explain why and suggest improvements.\n\nAnswers:\n"
        for i, ans in enumerate(answers, 1):
            prompt += f"{i}. {ans}\n"

        prompt += "\nWrite clear and concise feedback for each answer in English."

        # Wysyłka do OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert English teacher helping students improve their writing and reading skills."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        feedback_text = response['choices'][0]['message']['content']

        # Tworzenie PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Student Name: {student_name}", ln=True)
        pdf.cell(0, 10, f"Form: {form_name}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Feedback:\n\n{feedback_text}")

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        # Upload na Google Drive
        file_metadata = {
            'name': f"{student_name.replace(' ', '_')}_{form_name.replace(' ', '_')}.pdf",
            'parents': [FOLDER_ID],
            'mimeType': 'application/pdf'
        }
        media = MediaIoBaseUpload(pdf_output, mimetype='application/pdf')
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        # Zapisywanie do Google Sheets
        worksheet.append_row([student_name, form_name, json.dumps(answers), feedback_text])

        return jsonify({'message': 'Feedback generated and uploaded successfully!'}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
