from flask import Flask, logging, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

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

# เส้นทางหลักของเว็บแอป
@app.route('/')
def index():
    # แสดงหน้า HTML `index.html` จากโฟลเดอร์ templates
    return render_template('index.html')

# เส้นทาง API
@app.route("/test-api", methods=["POST"])
def test_api():
    # ดึงข้อมูล JSON จากคำขอ
    data = request.json
    print('request.json:', data)

    # ส่งข้อมูลกลับไปยังฝั่ง Frontend
    return jsonify({
        "status": "success",
        "received": data
    })

@app.route("/send-test-api-ai", methods=["POST"])
def send_test_api_ai():
    try:
        # ข้อความตัวอย่าง ที่ได้จาก POST
        user_input = request.json.get("message") 
        prompt = user_input
        print('prompt', prompt)
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

   
# ตรวจสอบว่าไฟล์นี้ถูกรันโดยตรง
if __name__ == "__main__":
    # เริ่มเซิร์ฟเวอร์ Flask บนพอร์ตที่กำหนด
    app.run(port=port, debug=True)
