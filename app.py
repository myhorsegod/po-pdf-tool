import streamlit as st
from pypdf import PdfReader
import pandas as pd
import re
from io import BytesIO

st.title("📄 PO PDF 轉 Excel 工具")

uploaded_files = st.file_uploader("上傳PDF訂單（可多個）", type="pdf", accept_multiple_files=True)


def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    return text


def extract_data(file):
    text = extract_text_from_pdf(file)

    data = []
    po_number = ""
    customer = ""

    # ✅ 抓 PO
    po_match = re.search(r'(PO[#\-\dA-Z]+)', text)
    if po_match:
        po_number = po_match.group(1)

    # ✅ 抓 customer
    lines = text.split("\n")
    for line in lines:
        if len(line.strip()) > 5 and ("Ltd" in line or "Limited" in line or "Company" in line):
            customer = line.strip()

    # ✅ 更寬鬆抓 item（這是重點）
    for line in lines:
        parts = line.split()

        if len(parts) >= 4:
            # 嘗試找到數字（quantity + price）
            numbers = [p for p in parts if re.match(r'^\d+(\.\d+)?$', p)]

            if len(numbers) >= 2:
                try:
                    qty = numbers[-2]
                    price = numbers[-1]

                    item_code = parts[0]
                    desc = " ".join(parts[1:-2])

                    data.append({
                        "Customer": customer,
                        "PO No": po_number,
                        "Item Code": item_code,
                        "Description": desc,
                        "Quantity": qty,
                        "Price": price
                    })
                except:
                    pass

    return data

if st.button("開始處理"):

    if not uploaded_files:
        st.warning("請先上傳PDF")
    else:
        all_data = []

        for file in uploaded_files:
            result = extract_data(file)
            all_data.extend(result)

        if not all_data:
            st.error("抓不到資料（PDF格式不同）")
        else:
            df = pd.DataFrame(all_data)

            st.success("✅ 解析完成")
            st.dataframe(df)

            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button(
                label="📥 下載 Excel",
                data=output,
                file_name="output.xlsx",
                mime="application/vnd.ms-excel"
            )