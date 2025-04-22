import re
import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from time import sleep

URL = "https://1000mostcommonwords.com/1000-most-common-french-words/"
OUT_CSV = "french_vocab_2000.csv"

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

def translate_to_japanese(words):
    from googletrans import Translator
    translator = Translator()
    translated_words = []
    print("日本語に翻訳中... (数分かかる場合があります)")
    
    for word in tqdm(words):
        try:
            translation = translator.translate(word, src='en', dest='ja')
            translated_words.append(translation.text)
            sleep(0.5)  # API制限を避けるため
        except Exception as e:
            print(f"翻訳エラー ({word}): {e}")
            translated_words.append(word)
    
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
        japanese_translations = translate_to_japanese(english_words)
        df["Back"] = japanese_translations

    # CSVファイルとして保存
    df.to_csv(OUT_CSV, index=False)
    print(f"✓ {OUT_CSV} を保存しました（{len(df)}個の単語カード）")

if __name__ == "__main__":
    main() 