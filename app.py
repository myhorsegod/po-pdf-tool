import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.title("📄 PO PDF 轉 Excel 工具")

uploaded_files = st.file_uploader("上傳PDF訂單（可多個）", type="pdf", accept_multiple_files=True)

def extract_data(file):
    data = []
    po_number = ""
    customer = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                # PO
                po_match = re.search(r'(PO\d+)', line)
                if po_match:
                    po_number = po_match.group(1)

                # Customer
                if "GmbH" in line or "Limited" in line:
                    customer = line.strip()

                # Item
                match = re.search(r'(\d{8,})\s+.*\s+(\d+)\s+Piece\s+([\d]+\.\d+)', line)

                if match:
                    parts = line.split()

                    try:
                        item_code = parts[1]
                        qty = parts[-4]
                        price = parts[-3]
                        desc = " ".join(parts[2:-4])

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
            st.error("抓不到資料（PDF格式可能不同）")
        else:
            df = pd.DataFrame(all_data)

            st.success("✅ 解析完成")
            st.dataframe(df)

            # Excel download
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button(
                label="📥 下載 Excel",
                data=output,
                file_name="output.xlsx",
                mime="application/vnd.ms-excel"
            )
