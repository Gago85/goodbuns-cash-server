from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import logging
import requests
from openpyxl import Workbook
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# 🔐 Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "вставь_сюда_токен")
CHAT_ID = os.getenv("CHAT_ID", "вставь_сюда_chat_id")
BASE_FOLDER = Path("D:/GoodbunsAIcash")

# 🧾 Создание Excel-файла
def create_excel(data, save_folder):
    wb = Workbook()
    ws = wb.active
    ws.title = "Кассовый отчёт"

    ws.append(["Дата", "Точка", "Наличные", "Безналичные", "Возврат (нал)", "Возврат (безнал)",
               "Итого", "Обеды", "Списание", "Комментарий"])
    ws.append([
        data.get("date", ""),
        data.get("point", ""),
        data.get("cash", ""),
        data.get("card", ""),
        data.get("return_cash", ""),
        data.get("return_card", ""),
        data.get("total", ""),
        data.get("lunches", ""),
        data.get("writeoff", ""),
        data.get("comment", "")
    ])

    filename = f"Кассовый отчёт - {data['point']} - {data['date']}.xlsx"
    filepath = save_folder / filename
    wb.save(filepath)
    return filepath, filename

# 💾 Сохраняем JSON копию
def save_json(data, save_folder, filename):
    json_path = save_folder / (filename.replace(".xlsx", ".json"))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 📤 Отправка в Telegram
def send_to_telegram(filepath):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(filepath, "rb") as file:
            response = requests.post(url, data={
                "chat_id": CHAT_ID,
                "caption": "💰 Новый кассовый отчёт"
            }, files={"document": file})

        logging.error(f"Telegram response: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Telegram send error: {str(e)}")
        return False

# 📥 Приём отчёта
@app.route("/submit_cash", methods=["POST"])
def handle_cash():
    try:
        data = request.form.to_dict()

        if not data.get("date"):
            data["date"] = datetime.now().strftime("%Y-%m-%d")

        date_folder = BASE_FOLDER / data["date"]
        date_folder.mkdir(parents=True, exist_ok=True)

        filepath, filename = create_excel(data, date_folder)
        save_json(data, date_folder, filename)
        sent = send_to_telegram(filepath)

        return jsonify({
            "status": "ok",
            "file": str(filepath),
            "telegram_sent": sent
        }), 200

    except Exception as e:
        error_text = f"❌ Ошибка: {str(e)}"
        print(error_text)
        logging.error(error_text)
        return jsonify({"status": "error", "message": str(e)}), 500

# 🔍 Просмотр последних ошибок
@app.route("/last_error", methods=["GET"])
def last_error():
    try:
        with open("errors.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "<br>".join(lines[-10:]) or "Нет ошибок"
    except Exception as e:
        return f"Ошибка чтения лога: {str(e)}"

# ⚙️ Логирование
logging.basicConfig(filename="errors.log", level=logging.ERROR, format="%(asctime)s - %(message)s")

# 🚀 Запуск
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
