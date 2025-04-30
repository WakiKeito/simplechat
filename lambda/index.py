# lambda/index.py
import json
import os
# import boto3
import urllib.request
import re  # 正規表現モジュールをインポート
import time
# from botocore.exceptions import ClientError


# Lambda コンテキストからリージョンを抽出する関数
# def extract_region_from_arn(arn):
#     # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
#     match = re.search('arn:aws:lambda:([^:]+):', arn)
#     if match:
#         return match.group(1)
#     return "us-east-1"  # デフォルト値

# グローバル変数としてクライアントを初期化（初期値）
# bedrock_client = None

# FastAPIのURLを取得
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://226a-34-16-146-87.ngrok-free.app/generate")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)

        # 会話履歴を使用
        messages = conversation_history.copy()
        # ユーザーメッセージを追加
        messages.append({"role": "user", "content": message})

        # 会話履歴からプロンプトを生成
        prompt_text = ""
        for msg in messages:
            if msg["role"] == "user":
                prompt_text += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt_text += f"Assistant: {msg['content']}\n"
        prompt_text += f"User: {message}\nAssistant:"

        # FastAPIに送信するペイロード
        request_payload = {
            "prompt": prompt_text,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        # FastAPIへリクエスト送信
        req = urllib.request.Request(
            url=FASTAPI_URL,
            data=json.dumps(request_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read().decode("utf-8"))
        end_time = time.time()

        print("FastAPI response:", json.dumps(response_body, indent=2))

        if "generated_text" not in response_body:
            raise Exception("FastAPI response missing 'generated_text'")

        assistant_response = response_body["generated_text"]
        response_time = response_body.get("response_time", round(end_time - start_time, 3))

        # アシスタントの応答を会話履歴に追加
        messages.append({"role": "assistant", "content": assistant_response})
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
