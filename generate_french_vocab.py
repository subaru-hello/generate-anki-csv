import re
import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from translator.client.client import TranslatorClient
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

URL = "https://1000mostcommonwords.com/1000-most-common-french-words/"
OUT_CSV = f"french_vocab_{datetime.now().strftime('%Y%m%d')}.csv"
BATCH_SIZE = 50  # 一度に翻訳する単語数

def download_word_list():
    print("フランス語単語リストをダウンロード中...")
    try:
        response = requests.get(URL, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"エラー: ダウンロード中に問題が発生しました: {e}")
        return None

def extract_words(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        return None
    
    words = []
    rows = table.find_all('tr')[1:]  # ヘッダーをスキップ
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            french = cols[1].text.strip()
            english = cols[2].text.strip()
            if french and english:
                words.append((french, english))
    
    return words

async def translate_batch(client, texts):
    try:
        return client.batch_translate(texts)
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return texts

async def translate_all_words(client, words):
    translated_words = []
    for i in range(0, len(words), BATCH_SIZE):
        batch = words[i:i+BATCH_SIZE]
        translated_batch = await translate_batch(client, batch)
        translated_words.extend(translated_batch)
    return translated_words

def main():
    # 単語リストのダウンロード
    html_content = download_word_list()
    if not html_content:
        return

    # 単語の抽出
    word_pairs = extract_words(html_content)
    if not word_pairs:
        print("単語を抽出できませんでした。")
        return

    # フランス語と英語の単語を分離
    french_words, english_words = zip(*word_pairs)

    # データフレームの作成
    df = pd.DataFrame({
        "Front": french_words,
        "Back": english_words,
        "POS": "",
        "Tags": "vocab3kyu"
    })

    # 日本語訳への変換（オプション）
    use_japanese = input("英語訳を日本語訳に変換しますか？ (y/n): ").lower() == 'y'
    if use_japanese:
        print("日本語に翻訳中...")
        client = TranslatorClient()
        try:
            translated_words = asyncio.run(translate_all_words(client, english_words))
            df["Back"] = translated_words
        finally:
            client.close()

    # CSVファイルとして保存
    df.to_csv(OUT_CSV, index=False)
    print(f"✓ {OUT_CSV} を保存しました（{len(df)}個の単語カード）")

if __name__ == "__main__":
    main() 