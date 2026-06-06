from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import anthropic
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
claude = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

SYSTEM_PROMPT = """คุณคือผู้ช่วยข้อมูลปฏิทินการศึกษา มหาวิทยาลัยอุบลราชธานี (UBU) ประจำปีการศึกษา 2569
ตอบเป็นภาษาไทยเสมอ กระชับ ชัดเจน

=== ปฏิทินการศึกษา UBU 2569 ===

ภาคต้น (1/2569):
- เปิดภาคเรียน: 8 มิ.ย. 69
- ลงทะเบียนเรียน: 11 พ.ค.-14 มิ.ย. 69
- สอบกลางภาค: 3-16 ส.ค. 69
- วันสุดท้ายของการเรียน: 4 ต.ค. 69
- สอบปลายภาค: 5-18 ต.ค. 69
- วันปิดภาคการศึกษา: 19 ต.ค. 69

ภาคปลาย (2/2569):
- เปิดภาคเรียน: 9 พ.ย. 69
- ลงทะเบียนเรียน: 19 ต.ค.-15 พ.ย. 69
- สอบกลางภาค: 11-22 ม.ค. 70
- วันสุดท้ายของการเรียน: 7 มี.ค. 70
- สอบปลายภาค: 8-19 มี.ค. 70
- วันปิดภาคการศึกษา: 20 มี.ค. 70

ภาคฤดูร้อน (3/2569):
- เปิดภาคเรียน: 5 เม.ย. 70
- ลงทะเบียนเรียน: 22 มี.ค.-11 เม.ย. 70
- สอบปลายภาค: 17-21 พ.ค. 70
- วันปิดภาคการศึกษา: 22 พ.ค. 70

กิจกรรมสำคัญ:
- รับนักศึกษาใหม่ TCAS 1-3: 1-3 มิ.ย. 69
- วันปฐมนิเทศนักศึกษาใหม่: 4 มิ.ย. 69
- วันสถาปนามหาวิทยาลัย: 30 ก.ค. 69
- พิธีพระราชทานปริญญาบัตร: ธ.ค. 69 - ม.ค. 70

ถ้าไม่มีข้อมูลในปฏิทิน ให้แจ้งว่าไม่มีข้อมูล และแนะนำให้ติดต่อสำนักบริการการศึกษา UBU"""

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    
    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_text}]
    )
    
    reply_text = response.content[0].text
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
