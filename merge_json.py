import json
import re

def merge_records(records):
    """
    担当者氏名が同じレコードをひとつに統合する。
    名前の前後および内部の空白（半角・全角）を除去して比較します。
    重複した場合は最初のレコードを採用します。
    """
    merged = {}
    for record in records:
        name = record.get("担当者氏名", "")
        # 前後の空白を除去し、すべての空白（半角・全角）を削除
        normalized_name = re.sub(r'\s+', '', name.strip())
        if normalized_name not in merged:
            merged[normalized_name] = record
        else:
            # 必要に応じて、他のフィールドもマージする処理を追加可能
            pass
    return list(merged.values())

def main():
    # 入力 JSON ファイルのパス（適宜変更してください）
    input_file = "QR_data.json"
    # 出力 JSON ファイルのパス（適宜変更してください）
    output_file = "merged_output.json"

    # JSON ファイルを読み込み
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # レコードを統合
    merged_data = merge_records(data)
    print("統合後のレコード数:", len(merged_data))

    # 統合結果を出力ファイルに保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    print(f"統合結果を {output_file} に出力しました。")

if __name__ == "__main__":
    main()