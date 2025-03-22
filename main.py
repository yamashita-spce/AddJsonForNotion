import json
import configparser as cp
import json
import creteNotionPerties as cnp
import re 
import argparse


def main():
    
    parser = argparse.ArgumentParser(description="Notion ページ作成/更新用 JSON ファイルを指定して実行します。")
    parser.add_argument("input_file", help="入力 JSON ファイルのパス")
    args = parser.parse_args()
    
    # 新規レコード群の読み込み
    with open(args, "r", encoding="utf-8") as f:
        new_records = json.load(f)

    print("既存ページをクエリ中...")
    db_response = cnp.query_database()

    existing_pages_list = []
    
    for page in db_response.get("results", []):
        profs = cnp.extract_page_info(page)  
        name = profs.get("担当者氏名")
        
        exist_flag = False

        if name:
            # 既に同じメールがリスト内に存在するか確認
            for p in existing_pages_list:
                p = re.sub(r'\s', '', p.get("担当者氏名"))
                if p == name:
                    exist_flag = True
                    break
        
        if exist_flag == False:
            existing_pages_list.append(profs)
    
    print(f"既存ページ: {len(existing_pages_list)}")

    new = 0
    updated = 0
    
    # # # # 各レコードを処理
    for record in new_records:
        name = re.sub(r'\s', '', record.get("担当者氏名")) 
        
        exit_flag = False

        for existing_page in existing_pages_list:
            exist_name = re.sub(r'\s', '', existing_page.get("担当者氏名"))
            
            if exist_name == name:
                exit_flag = True
                
                if record.get("商談メモ") == "":
                    print("[*] 商談メモが空のため、アップデートをスキップします。")
                    break
                
                print(f"[*]既存ページを更新します。")
                cnp.update_page(existing_page["page_id"], record.get("商談メモ"))
                updated += 1
                break    
                
        if exit_flag == False:    
            print("[*]新規ページを作成します。")
                
            property = cnp.build_notion_properties(record)
            cnp.create_notion_page(property)
            new += 1

    
    print(f"既存ページを{updated}件更新しました。")
    print(f"新規ページを{new}件作成しました。")


if __name__ == "__main__":
    main()
