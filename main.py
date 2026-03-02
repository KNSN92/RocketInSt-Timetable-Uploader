import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import streamlit as st
import pandas as pd
import ocr

RocketInStToken = os.getenv("RocketInStToken")
url = "https://rocket-in-st.vercel.app/api/timetable"

# webui
async def main():
    st.write("# uploader")
    uploaded_img = st.file_uploader("Upload", type=["png"])
    if uploaded_img:
        st.image(uploaded_img)
        test = os.path.join("./TimeTableImages", uploaded_img.name)
        with open(test, "wb") as f:
            f.write(uploaded_img.read())
            print("画像保存")
        print("ocr開始")
        df = await ocr.ocr(test)
        print("ocr終了")
        st.dataframe(df)



if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

def upload_time_table():
    headers = {
        'Authorization': f'Bearer {RocketInStToken}'
    }
    timetable = df.to_dict()
    for room, lessons in timetable.items():
        timetable[room] = {
            period : title for period, title in lessons.items() if title is not None
        }
    timetable_json = json.dumps(timetable, ensure_ascii=False)
    print(timetable_json)
    res = requests.post(url, headers=headers, data=timetable_json)
    print(res)
