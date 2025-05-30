from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import openpyxl
from openpyxl.styles import Font, Alignment
import requests
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
CORS(app)

SAVE_FOLDER = "cash_reports"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

def create_excel(data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Касса"

    headers = [
        "Дата", "Точка", "Наличные", "Безналичные",
        "Возврат (нал)", "Возврат (безнал)", "Итого", "Обеды (₽)", "Списание (₽)"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    row = [
        data.get("date"),
        data.get("point"),
        float(data.get("cash", 0)),
        float(data.get("card", 0)),
        float(data.get("return_cash", 0)),
        float(data.get("return_card", 0)),
        float(data.get("total", 0)),
        float(data.get("lunches", 0)),
        float(data.get("writeoff", 0))
    ]
    ws.append(row)

    filename = f"Кассовый отчёт - {data.get('point')} - {data.get('date')}.xlsx"
    filepath = os.path.join(SAVE_FOLDER, filename)
    wb.save(filepath)
    return filepath

def send_to_telegram(filepath):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(filepath, "rb") as file:
        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "caption": "💰 Новый кассовый отчёт"
        }, files={"document": file})
    return response.status_code == 200

@app.route("/submit_cash", methods=["POST"])
def handle_cash():
    try:
        data = request.form
        filepath = create_excel(data)
        sent = send_to_telegram(filepath)
        return jsonify({"status": "ok", "file": filepath, "telegram_sent": sent}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

