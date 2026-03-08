# yomitokuと前処理とかのライブラリのインポート
from yomitoku import DocumentAnalyzer
from yomitoku.export.export_csv import table_to_csv
from yomitoku.data.functions import load_image
from yomitoku.utils.visualizer import reading_order_visualizer
import numpy as np
import torch
import cv2
from multiprocessing import freeze_support

# その他のライブラリのインポート
import time
from pprint import pprint
from IPython.display import display
from PIL import Image
import pandas as pd
import json
# yomitokuがマルチプロセスを使う為、freeze_supportを呼び出す
freeze_support()

# 変数の設定
# 下記のパスを書き換えると読み取る画像を変更できる
# img_path = "./images/image7.png"
# dict名 = {'修正前1': '修正後1', '修正前2': '修正後2'}
# 読み取りミス修正用dict
miss = {
    'Na': 'Nα','Np': 'Nβ', 'Nv': 'Nγ'
    }
# 時間
period_ja_to_en = {
    "朝": "Morning",
    "朝礼": "MorningMeeting",
    "1限": "FirstPeriod",
    "2限": "SecondPeriod",
    "3限": "ThirdPeriod",
    "昼休み": "NoonRecess",
    "4限": "FourthPeriod",
    "5限": "FifthPeriod",
    "6限": "SixthPeriod",
    "終礼": "ClosingMeeting",
    "放課後": "AfterSchool",
}
# 部屋名と時間割名の定数を定義
ROOM_NAMES = ["大広間", "秘密基地", "万里", "7階"]
TIME_SLOTS = ["朝", "朝礼", "1限", "2限", "3限", "昼休み", "4限", "5限", "6限", "終礼", "放課後"]

# デバイスの設定
# MPSはyomitokuのバグで使えないけどgithubでプルリクが承認されたので、近々使えるようになるはず。
# 簡単な修正だからpatchを適用しても良いけど面倒いからね〜
async def ocr(img_name: str, img_path: str):
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Using device: {device}")

    # 画像を読み取ってグレースケールに変換
    img = load_image(img_path)[0]

    print(img.shape)

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    # OCRの実行関数の定義
    # yomitokuのanalyzerは__call__で実行出来るけど内部でasyncio.runを使っているので、jupyter notebook上で直接実行できない。
    # なので、async関数を定義してから実行する形にする。

    async def analyze(img: np.ndarray):
        analyzer = DocumentAnalyzer(device=device, visualize=True, configs={})
        analyzer.img = img
        resutls, ocr, layout = await analyzer.run(img)

        if analyzer.visualize:
            layout = reading_order_visualizer(layout, resutls)

        return resutls, ocr, layout
    # OCRの実行
    start = time.time()
    results, img, layout = await analyze(img)
    end = time.time()
    print(f"OCR Time: {end - start} seconds")


    # テーブルの中身が空だったとき用？
    if len(results.tables) == 0:
        print("No tables found.")
    table = table_to_csv(results.tables[0], ignore_line_break=False)
    # pprint(table)
    df = pd.DataFrame(table)

    df.to_json(f"TimeTableCsvs/{img_name}_raw.csv", force_ascii=False)

    # 年月日パターンを含むセルの行と列を特定
    date_pattern = r"\d{4}年\d{1,2}月\d{1,2}日"
    mask = df.apply(lambda col: col.astype(str).str.contains(date_pattern, na=False))
    date_positions = np.argwhere(mask.values)
    if len(date_positions) == 0:
        raise ValueError("年月日が見つかりませんでした")
    date_row_pos, date_col_pos = date_positions[0]
    print(f"年月日の位置: 行={df.index[date_row_pos]}, 列={df.columns[date_col_pos]}")

    # 年月日より上の行と左の列をdrop
    df = df.iloc[date_row_pos:, date_col_pos:]
    # 空文字をNaNに置換し、全て空の行と列を削除
    df = df.replace("", np.nan).dropna(how="all").dropna(axis=1, how="all").fillna("")
    if df.shape[1] != len(ROOM_NAMES)+1:
        print("Table format is unexpected. Trying to adjust...")
        df = df.iloc[:, :len(ROOM_NAMES)+1]

    df.columns=["時間"] + ROOM_NAMES
    df = df.set_index("時間")
    df = df.replace("\n", " ", regex=True)

    # 上記のdictを使用した読み取りミスの修正
    for k, v in miss.items():
        df = df.replace(k,v, regex=True)
    # 時間を変換
    df = df.rename(index=period_ja_to_en)
    # 重複を削除
    df = df[~df.index.duplicated()]
    # nanをNoneにする
    df = df.replace([np.nan], [None])
    # jsonにアウトプット
    df.to_json(f"TimeTableCsvs/{img_name}_out.csv", force_ascii=False)
    return df
