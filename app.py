from flask import Flask, request, jsonify
import openai
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Load Google Sheets credentials
gc = gspread.service_account(filename="credentials.json")
sh = gc.open("StudentFeedback")  # <-- podmienisz na swoją nazwę arkusza
worksheet = sh.sheet1

@app.route('/')
def home():
    return "Auto Feedback Bot is running!"

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')

    prompt = f"Question: {question}\nStudent Answer: {answer}\nEvaluate the answer, give short and precise feedback in English."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful and concise English teacher."},
            {"role": "user", "content": prompt}
        ]
    )

    feedback_text = response['choices'][0]['message']['content'].strip()
    return jsonify({"feedback": feedback_text})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)