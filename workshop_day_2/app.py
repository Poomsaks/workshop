from flask import Flask, logging, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import re
import uuid
import json
import fitz
import requests

load_dotenv()

# เริ่มต้นแอป Flask
app = Flask(__name__)
# กำหนดพอร์ตสำหรับแอป
port = 3000

api_key = os.getenv("GEMINI_API_KEY", "GEMINI_API_KEY")
MODEL = "gemini-1.5-flash"
# MODEL = 'gemini-pro'

genai.configure(api_key=api_key)
logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = os.path.abspath("workshop_day_2/doc")


# เส้นทางหลักของเว็บแอป
@app.route("/")
def index():
    # แสดงหน้า HTML `index.html` จากโฟลเดอร์ templates
    return render_template("index.html")

# เส้นทาง API test-api
@app.route("/test-api", methods=["POST"])
def test_api():
    # ดึงข้อมูล JSON จากคำขอ
    data = request.json
    print("request.json:", data)

    # ส่งข้อมูลกลับไปยังฝั่ง Frontend
    return jsonify({"status": "success", "received": data})

# เส้นทาง API send-test-api-ai
@app.route("/send-test-api-ai", methods=["POST"])
def send_test_api_ai():
    try:
        # ข้อความตัวอย่าง ที่ได้จาก POST
        user_input = request.json.get("message")
        prompt = user_input
        print("prompt", prompt)
        # สร้างโมเดลและสร้างคำตอบ
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        # พิมพ์ผลลัพธ์ในคอนโซล
        print("Generated response:", response.text)
        # ส่งคำตอบกลับไปยังผู้เรียก API
        return jsonify({"response": response.text}), 200
    except Exception as e:
        # จัดการข้อผิดพลาดและส่งกลับ
        print("Error generating response:", str(e))
        return jsonify({"error": "Unable to generate response", "details": str(e)}), 500

# ฟังก์ชันสำหรับดึงข้อมูลจากไฟล์ในโฟลเดอร์
def load_files_from_folder(folder_path):
    data = []
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    data.append(file.read())
    except Exception as e:
        print("Error loading files:", str(e))
    return data

# เส้นทาง API send-api-ai-from-file
@app.route("/send-api-ai-from-file", methods=["POST"])
def send_api_ai_from_file():
    try:
        # ข้อความตัวอย่าง ที่ได้จาก POST
        user_input = request.json.get("message")
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # โหลดข้อมูลจาก UPLOAD_FOLDER
        context_data = load_files_from_folder(UPLOAD_FOLDER)
        if not context_data:
            return jsonify({"error": "No context data found in UPLOAD_FOLDER"}), 500

        # ตรวจสอบคำถามที่เกี่ยวข้องกับข้อมูลใน
        context = "\n".join(context_data)
        prompt = f"Context: {context}\nUser Input: {user_input}\nตอบเป็นภาษาไทย:"
        print("Prompt:", prompt)

        # สร้างโมเดลและสร้างคำตอบ
        model = genai.GenerativeModel(MODEL)  # แทนที่ "MODEL_NAME" ด้วยโมเดลของคุณ
        response = model.generate_content(prompt)

        print("Generated response:", response.text)

        # ส่งคำตอบกลับไปยังผู้เรียก API
        return jsonify({"response": response.text}), 200
    except Exception as e:
        # จัดการข้อผิดพลาดและส่งกลับ
        print("Error generating response:", str(e))
        return jsonify({"error": "Unable to generate response", "details": str(e)}), 500

history = []

# เส้นทาง API send-api-ai-from-history
@app.route("/send-api-ai-from-history", methods=["POST"])
def send_api_ai_from_history():
    try:
        # ข้อความตัวอย่าง ที่ได้จาก POST
        user_input = request.json.get("message")
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # เก็บคำถามและคำตอบในหน่วยความจำ
        context = "\n".join([f"User: {q['question']}\nAI: {q['response']}" for q in history])

        # สร้าง prompt ด้วยข้อมูล context ที่เก็บคำถามและคำตอบก่อนหน้า
        prompt = f"Context: {context}\nUser Input: {user_input}\nตอบเป็นภาษาไทย:"
        print("Prompt:", prompt)

        # สร้างโมเดลและสร้างคำตอบ
        model = genai.GenerativeModel(MODEL)  # แทนที่ "MODEL_NAME" ด้วยโมเดลของคุณ
        response = model.generate_content(prompt)

        print("Generated response:", response.text)

        # เพิ่มคำถามและคำตอบในหน่วยความจำ
        history.append({"question": user_input, "response": response.text})

        # ส่งคำตอบกลับไปยังผู้เรียก API
        return jsonify({"response": response.text}), 200
    except Exception as e:
        # จัดการข้อผิดพลาดและส่งกลับ
        print("Error generating response:", str(e))
        return jsonify({"error": "Unable to generate response", "details": str(e)}), 500

# ฟังก์ชันสำหรับดึงข้อความจากไฟล์ PDF
def extract_text_from_pdf(file_bytes):
    text = ""
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    pdf_document.close()
    return text

# ฟังก์ชันสำหรับแบ่งข้อความออกเป็นส่วนเล็ก ๆ (chunk)
def split_text_into_chunks(text, chunk_size):
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 <= chunk_size:
            current_chunk += word + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = word + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

# ฟังก์ชันสำหรับสร้างคำถาม
def generate_question(context):
    if len(context.strip()) == 0:
        return "What information is provided in this text?"

    if "summary" in context.lower():
        return f"What is the summary of the information provided? (Context: {context[:50]}...)"
    elif "result" in context.lower():
        return f"What result does this text describe? (Context: {context[:50]}...)"
    elif "analysis" in context.lower():
        return f"What analysis is presented in this text? (Context: {context[:50]}...)"
    else:
        return f"What information does this text provide? (Context: {context[:50]}...)"

# เส้นทาง API uploadFileAi
@app.route("/uploadFileAi", methods=["POST"])
def upload_file_ai():
    # ตรวจสอบว่าการร้องขอเป็นแบบ POST หรือไม่
    if request.method == "POST":
        try:
            # ดึงไฟล์ที่ผู้ใช้อัปโหลด
            uploaded_file = request.files.get("file")
            text = ""  # ตัวแปรสำหรับเก็บข้อความที่ดึงจากไฟล์
            # ตรวจสอบว่ามีไฟล์ที่ถูกอัปโหลดหรือไม่
            if uploaded_file:
                # ดึงนามสกุลของไฟล์ และเนื้อหาในรูปแบบไบต์
                file_extension = uploaded_file.filename.rsplit(".", 1)[-1].lower()
                file_bytes = uploaded_file.read()
                # ลบช่องว่างส่วนเกินในข้อความ (เผื่อไว้ในกรณีข้อความมีอยู่แล้ว)
                text = re.sub(r"\s+", " ", text)
                # ตรวจสอบประเภทไฟล์ หากเป็น PDF ให้ดึงข้อความด้วย extract_text_from_pdf
                if file_extension == "pdf":
                    text = extract_text_from_pdf(file_bytes)
                else:
                    # หากไม่ใช่ PDF หรือไฟล์เสีย ให้แจ้งว่าไม่รองรับ
                    return "Unsupported file format or file may be corrupted. Please check the file and try again."
            # แบ่งข้อความเป็น chunk ย่อย โดยกำหนดขนาด chunk สูงสุด 100 ตัวอักษร
            chunks = split_text_into_chunks(text, 100)
            # สร้างรายการ JSONL จาก chunk
            jsonl_data = []
            for chunk in chunks:
                jsonl_data.append(
                    {
                        "id": str(uuid.uuid4()),  # สร้าง UUID สำหรับแต่ละ chunk
                        "context": chunk,  # ข้อความใน chunk
                        "question": generate_question(chunk),  # สร้างคำถามจาก chunk
                    }
                )
            # ตรวจสอบว่ามีข้อมูล JSONL ที่ต้องบันทึกหรือไม่
            if jsonl_data:
                # กำหนดชื่อไฟล์สำหรับบันทึกข้อมูล JSONL
                original_filename = (
                    uploaded_file.filename.rsplit(".", 1)[0]
                    if uploaded_file
                    else "scraped_data"
                )
                output_path = os.path.join(UPLOAD_FOLDER, f"{original_filename}.jsonl")
                # บันทึกข้อมูล JSONL ลงไฟล์ในโฟลเดอร์ที่กำหนด
                with open(output_path, "w", encoding="utf-8") as f:
                    for item in jsonl_data:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                # แสดงรายชื่อไฟล์ทั้งหมดในโฟลเดอร์
                files_list = os.listdir(UPLOAD_FOLDER)
                files_list_html = "".join(
                    [
                        f'<input type="checkbox" value="{file}" id="{file}"><label for="{file}">{file}</label><br>'
                        for file in files_list
                    ]
                )
                # ส่งข้อความแจ้งความสำเร็จ และรายชื่อไฟล์ที่มีอยู่
                return f"File processed successfully! Saved to {output_path}<br><br>Files in directory:<br>{files_list_html}"
            else:
                # หากไม่มีข้อมูลที่ต้องบันทึก ให้ส่งข้อความแจ้ง
                return "No data to save."

        except Exception as e:
            # หากเกิดข้อผิดพลาดระหว่างการประมวลผล ส่งข้อความแสดงข้อผิดพลาด
            return (
                jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}),
                500,
            )

    # หากการร้องขอไม่ใช่ POST หรือไม่มีไฟล์ที่อัปโหลด
    return (
        jsonify(
            {
                "status": "error",
                "message": "Invalid request method or no file uploaded!",
            }
        ),
        400,
    )


# เส้นทาง WebHook Line
@app.route("/sendMessageAI", methods=["POST"])
def sendMessageAI():
    data = request.get_json()
    events = data.get("events", [])
    print(f'events: {events}')
    for event in events:
        if event.get("message") and event["message"].get("text"):
            reply_token = event["replyToken"]
            user_id = event["source"]["userId"]
            user_message = event["message"]["text"]
            
            # ข้อมูลที่ส่งไปยัง Line API
            payload = {
                "to": user_id,  # ระบุ ID ของผู้รับที่ต้องการส่งข้อความ
                "messages": [
                    {
                        "type": "text",
                        "text": "Hello, world1"
                    },
                    {
                        "type": "text",
                        "text": "Hello, world2"
                    }
                ]
            }

            # กำหนด Headers สำหรับ Authorization
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {channel access token}"  # ใส่ channel access token ของคุณที่นี่
            }

            # ส่งคำขอไปยัง LINE API
            response = requests.post("https://api.line.me/v2/bot/message/push", json=payload, headers=headers)
            
            # ตรวจสอบสถานะการส่ง
            if response.status_code == 200:
                print("Message sent successfully")
                return jsonify({"status": "success", "received": data})
            else:
                print(f"Failed to send message: {response.text}")
                return jsonify({"status": "error", "message": response.text})

# เส้นทาง WebHook Line ที่ใช้ AI
@app.route("/messageFromAI", methods=["POST"])
def messageFromAI():
    data = request.get_json()
    events = data.get("events", [])
    print(f'events: {events}')
    for event in events:
        if event.get("message") and event["message"].get("text"):
            reply_token = event["replyToken"]
            user_id = event["source"]["userId"]
            user_message = event["message"]["text"]
            
            # ข้อความตัวอย่าง ที่ได้จาก POST
            user_input = user_message
            prompt = user_input
            print("prompt", prompt)
            # สร้างโมเดลและสร้างคำตอบ
            model = genai.GenerativeModel(MODEL)
            response = model.generate_content(prompt)
            # พิมพ์ผลลัพธ์ในคอนโซล
            print("Generated response:", response.text)
    
            # ข้อมูลที่ส่งไปยัง Line API
            payload = {
                "to": user_id,  # ระบุ ID ของผู้รับที่ต้องการส่งข้อความ
                "messages": [
                    {
                        "type": "text",
                        "text": response.text
                    }
                ]
            }

            # กำหนด Headers สำหรับ Authorization
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {channel access token}"  # ใส่ channel access token ของคุณที่นี่
            }

            # ส่งคำขอไปยัง LINE API
            response = requests.post("https://api.line.me/v2/bot/message/push", json=payload, headers=headers)
            
            # ตรวจสอบสถานะการส่ง
            if response.status_code == 200:
                print("Message sent successfully")
                return jsonify({"status": "success", "received": data})
            else:
                print(f"Failed to send message: {response.text}")
                return jsonify({"status": "error", "message": response.text})

# ตรวจสอบว่าไฟล์นี้ถูกรันโดยตรง
if __name__ == "__main__":
    # เริ่มเซิร์ฟเวอร์ Flask บนพอร์ตที่กำหนด
    app.run(port=port, debug=True)
