import streamlit as st
from pypdf import PdfReader
import pandas as pd
from io import BytesIO
import openai
import json

# ✅ 設定 API Key（在 Streamlit Secrets 設定）
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("📄 PO PDF 轉 Excel 工具（AI版）")

uploaded_files = st.file_uploader(
    "上傳PDF訂單（可多個）",
    type="pdf",
    accept_multiple_files=True
)

# ✅ 讀PDF文字
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


# ✅ AI解析（核心）
def extract_with_ai(text):

    prompt = f"""
    Extract structured data from this purchase order.

    Return ONLY JSON in this format:

    {{
      "customer_name": "...",
      "po_number": "...",
      "items": [
        {{
          "item_code": "...",
          "description": "...",
          "quantity": "...",
          "price": "..."
        }}
      ]
    }}

    Rules:
    - Do not include explanations
    - If missing, leave blank
    - Keep numbers clean

    TEXT:
    {text[:12000]}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract structured data from documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        result = response["choices"][0]["message"]["content"]

        return json.loads(result)

    except Exception as e:
        st.error(f"AI 解析錯誤: {e}")
        return None


# ✅ 主解析流程
def extract_data(file):
    text = extract_text_from_pdf(file)

    ai_result = extract_with_ai(text)

    data = []

    if not ai_result:
        return data

    customer = ai_result.get("customer_name", "")
    po_number = ai_result.get("po_number", "")

    for item in ai_result.get("items", []):
        data.append({
            "Customer": customer,
            "PO No": po_number,
            "Item Code": item.get("item_code", ""),
            "Description": item.get("description", ""),
            "Quantity": item.get("quantity", ""),
            "Price": item.get("price", "")
        })

    return data


# ✅ UI 按鈕
if st.button("開始處理"):

    if not uploaded_files:
