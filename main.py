import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import asyncio
import streamlit as st
import pandas as pd
import ocr

RocketInStToken = os.getenv("RocketInStToken")
url = "https://rocket-in-st.vercel.app/api/timetable"

def upload_time_table(df: pd.DataFrame):
    headers = {
        'Authorization': f'Bearer {RocketInStToken}'
    }
    timetable = df.to_dict()
    for room, lessons in timetable.items():
        timetable[room] = {
            period : title for period, title in lessons.items() if title is not None
        }
    timetable_json = json.dumps(timetable, ensure_ascii=False)
    res = requests.post(url, headers=headers, data=timetable_json)
    print(res.text)

# session stateの初期化
if "df" not in st.session_state:
    st.session_state.df = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

# webui
st.write("# uploader")
uploaded_img = st.file_uploader("Upload", type=["png"])

if uploaded_img:
    st.image(uploaded_img)

    # 別の画像がアップロードされたら状態をリセット
    if st.session_state.uploaded_filename != uploaded_img.name:
        st.session_state.df = None
        st.session_state.uploaded_filename = uploaded_img.name

    # OCRがまだ実行されていない場合のみ実行
    if st.session_state.df is None:
        img_path = os.path.join("./TimeTableImages", uploaded_img.name)
        with open(img_path, "wb") as f:
            f.write(uploaded_img.read())
        with st.spinner("OCR in progress..."):
            st.session_state.df = asyncio.run(ocr.ocr(uploaded_img.name, img_path))
        st.rerun()

    st.success("OCR completed!")
    edited_df = st.data_editor(st.session_state.df)
    if st.button("Upload TimeTable"):
        upload_time_table(edited_df)
        st.success("Uploaded!")
else:
    # 画像が削除されたら状態をリセット
    st.session_state.df = None
    st.session_state.uploaded_filename = None
