import os
import json
import openai
import gspread
from flask import Flask
from google.oauth2.service_account import Credentials
from fpdf import FPDF

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

# Otwieramy arkusz
sh = gc.open("Maths Calculator (Responses)")  # <-- Upewnij się, że nazwa arkusza jest poprawna
worksheet = sh.sheet1

# Tworzymy aplikację Flask
app = Flask(__name__)

# Ścieżka zapisu PDF
EVIDENCE_FOLDER = "./evidence"

if not os.path.exists(EVIDENCE_FOLDER):
    os.makedirs(EVIDENCE_FOLDER)

@app.route('/', methods=['GET'])
def home():
    return "Auto Feedback Bot is running!"

@app.route('/generate_feedback', methods=['POST'])
def generate_feedback():
    try:
        # Pobieramy wszystkie odpowiedzi
        records = worksheet.get_all_records()

        # Pobieramy tytuł formularza (nazwa arkusza)
        form_title = sh.title

        for record in records:
            student_name = record.get('Name', 'Unknown Student')
            answers = []

            # Pomijamy pola typu Timestamp lub Name
            for key, value in record.items():
                if key.lower() not in ['timestamp', 'name']:
                    answers.append(f"{key}: {value}")

            # Tworzymy prompt
            prompt = f"""Evaluate the following student's answers to a math exam based on these detailed correct answers and marking rules:

{open('instructions.txt').read()}

Student's answers:
"""
            for answer in answers:
                prompt += f"{answer}\n"

            prompt += "\nPlease generate specific, constructive feedback for each question. Write in English. Be clear, but concise."

            # Wysyłamy do OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Math examiner providing student feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            feedback_text = response['choices'][0]['message']['content']

            # Tworzymy PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(0, 10, f"Student: {student_name}", ln=True)
            pdf.cell(0, 10, f"Form: {form_title}", ln=True)
            pdf.ln(10)

            for line in feedback_text.split('\n'):
                pdf.multi_cell(0, 10, line)

            pdf_filename = f"{EVIDENCE_FOLDER}/{student_name.replace(' ', '_')}_{form_title.replace(' ', '_')}.pdf"
            pdf.output(pdf_filename)

        return {"message": "All feedback generated successfully!"}, 200

    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
