import datetime
import requests
import configparser
import os
import chat_api
import re

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

# Notion 
USER = "DEFAULT"
# USER = "PRIVATE"

NOTION_API_TOKEN = config[USER]["NOTION_API_TOKEN"]
DATABASE_ID = config[USER]["DATABASE_ID"]  # NotionデータベースIDの部分のみ
NOTION_VERSION = config[USER]["NOTION_VERSION"]


# 共通ヘッダーの設定
headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def extract_plain_text(rich_text_list):
    """
    Notion API の rich_text オブジェクトのリストから、
    各要素の plain_text を連結した文字列を返す
    """
    if not rich_text_list:
        return ""
    return "".join(item.get("plain_text", "") for item in rich_text_list)


def extract_page_info(page):
    """
    1ページ分の必要な情報のみを抽出する。
    - page_id: ページID（更新時に必要）
    - メール: 重複チェックのキーとして利用
    - 商談メモ: 更新対象のフィールド
    - 担当: 更新対象
    """
    props = page.get("properties", {})
    name = props.get("担当者氏名").get("rich_text", "")[0].get("text").get("content")
    name = re.sub(r'\s', '', name)
    
    return {
        "page_id": page.get("id"),
        "担当者氏名": name,
    }


def query_database():
    """
    Notion データベース内の既存ページをクエリして取得する
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {}  # 必要に応じてフィルタ等を追加可能
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


# notion データベースプロパティの組み立て
def build_notion_properties(business_card_data):
    
    # 業種、部署、役職を推論
    response = chat_api.openAPI(business_card_data)
    
    # リード獲得日の変換（例："2025/3/12" → "2025-03-12T00:00:00"）
    lead_date = None
    try:
        date = business_card_data.get("リード獲得日", "").strip()
        dt = datetime.datetime.strptime(date, "%Y/%m/%d %H:%M")
        lead_date = dt.strftime("%Y-%m-%dT%H:%M:%S")
        # print("リード獲得日:", lead_date)
        
    except Exception as e:
        print(f"リード獲得日のパースエラー: {e}")
        lead_date = None

    properties = {}

    # ▼ 会社名: Title 型
    # Notion 側で「会社名」が title プロパティとして定義されている場合、
    # 空なら "title": []、値があれば "title": [ { "type": "text", "text": {"content": ...} } ]
    company = business_card_data.get("会社名", "").strip()
    if company:
        properties["会社名"] = {
            "title": [
                {
                    "type": "text",
                    "text": {"content": company}
                }
            ]
        }
    else:
        properties["会社名"] = {"title": []}
    
    # ▼ 担当者氏名: Rich text 型
    # Notion 側で「担当者氏名」が rich_text なら、以下のようにする
    name = business_card_data.get("担当者氏名", "").strip()
    if name:
        properties["担当者氏名"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": name}
                }
            ]
        }
    else:
        properties["担当者氏名"] = {"rich_text": []}

    # ▼ 業種: select 型
    industry = response.get("業種", "").strip()
    if industry:
        properties["業種"] = {"select": {"name": industry}}
    else:
        properties["業種"] = {"select": None}

    # ▼ 部署: multi_select 型
    department = response.get("部署", "").strip()
    if department:
        properties["部署"] = {"multi_select": [{"name": department}]}
    else:
        properties["部署"] = {"multi_select": []}

    # ▼ 正式部署名: Rich text 型
    dept_raw = business_card_data.get("正式部署名", "").strip()

    if dept_raw:
        properties["正式部署名"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": dept_raw}
                }
            ]
        }
    else:
        properties["正式部署名"] = {"rich_text": []}

    # ▼ 役職: multi_select 型
    title_inferred = response.get("役職", "").strip()
    if title_inferred:
        properties["役職"] = {"multi_select": [{"name": title_inferred}]}
    else:
        properties["役職"] = {"multi_select": []}

    # ▼ 役職区分: rich_text 型
    role_raw = business_card_data.get("役職区分", "").strip() or title_inferred
    if role_raw:
        properties["役職区分"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": role_raw}
                }
            ]
        }
    else:
        properties["役職区分"] = {"rich_text": []}

    # ▼ 電話番号: phone_number 型
    phone = business_card_data.get("電話番号", "").strip()
    if phone:
        properties["電話番号"] = {"phone_number": phone}
    else:
        properties["電話番号"] = {"phone_number": None}

    # ▼ メール: email 型
    email = business_card_data.get("E-mail", "").strip()
    if email:
        properties["メール"] = {"email": email}
    else:
        properties["メール"] = {"email": None}

    # ▼ リード獲得日: date 型
    if lead_date:
        properties["リード獲得日"] = {"date": {"start": lead_date}}
    else:
        properties["リード獲得日"] = {"date": None}
    
    # ▼ 商談メモ: rich_text 型
    memo = business_card_data.get("商談メモ", "").strip()
    if memo:
        properties["商談メモ"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": memo}
                }
            ]
        }
    else:
        properties["商談メモ"] = {"rich_text": []}
    
    # ▼ 担当: multi_select 型
    # 担当者の名前をリストで指定する
    owner = response.get("担当", "").strip()
    if owner:
        properties["担当"] = {"multi_select": [{"name": owner}]}
    else:
        properties["担当"] = {"multi_select": []}
    

    # ▼ 以下、空欄の項目は Notion の型に合わせたデフォルト値
    properties["タグ"] = {"select": {"name": "DXPO大阪'25"}}
    properties["ステータス"] = {"status": None}
    properties["ペルソナ"] = {"select": None}
    properties["商談ステータス"] = {"status": None}
    properties["次アクション"] = {"rich_text": []}
    properties["BANT"] = {"rich_text": []}
    properties["契約開始日"] = {"date": None}
    properties["製品"] = {"multi_select": []}
    properties["契約プラン"] = {"select": None}
    properties["料金形態"] = {"select": None}
    properties["割引"] = {"number": None}
    properties["契約ステータス"] = {"select": None}
    properties["自動更新"] = {"checkbox": False}
    properties["チームID"] = {"rich_text": []}
    properties["クレーム"] = {"rich_text": []}
    properties["解約理由"] = {"rich_text": []}

    # ▼ 郵便番号: rich_text 型
    zipcode = business_card_data.get("郵便番号", "").strip()
    if zipcode:
        properties["郵便番号"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": zipcode}
                }
            ]
        }
    else:
        properties["郵便番号"] = {"rich_text": []}

    # ▼ 都道府県: rich_text 型
    dist = business_card_data.get("都道府県", "").strip()
    prefecture = ""
    if dist:
        # アドレスの先頭要素だけ取り出す実装例（自由に変更可）
        parts = dist.split()
        prefecture = parts[0] if parts else ""
    if prefecture:
        properties["都道府県"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": prefecture}
                }
            ]
        }
    else:
        properties["都道府県"] = {"rich_text": []}

    # ▼ 住所: rich_text 型
    address = business_card_data.get("住所", "").strip()
    if address:
        properties["住所"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": address}
                }
            ]
        }
    else:
        properties["住所"] = {"rich_text": []}
    
    # 情報源: select 型
    properties["情報源"] = {"select": {"name": "QR"}}

    # ▼ デバッグ出力
    # print("=== DEBUG: properties ===")
    # for k, v in properties.items():
    #     print(k, v)
    # print("=== end of debug ===")

    return properties


def create_notion_page(properties):
    """
    Notion API を呼び出してページを作成する関数。
    """
    url = "https://api.notion.com/v1/pages"
 
    # 本文に追加するブロックを定義
    children = []
    body_text = "[*] QR情報から取得しました。名刺はありません."
    
    if body_text:
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": body_text
                            }
                        }
                    ]
                }
            }
        ]
    
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties,
        "children": children
    }
    
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("[*]Notionページの作成に成功しました。")
        page = response.json()
        return page.get("id")
    else:
        print(f"Notionページ作成エラー: {response.text}")



def update_page(page_id, new_memo):
    """
    引数で受け取った page_id の「商談メモ」プロパティを更新する
    """
    
    # 1) 商談メモの更新
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    # Notion の rich_text プロパティに合わせた構造
    payload = {
        "properties": {
            "商談メモ": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": new_memo
                        }
                    }
                ]
            }
        }
    }
    
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()  # エラー時は例外を発生させる
    print(f"[*] Page {page_id} updated: 商談メモ => {new_memo}")
    
    
    # 2) ページ本文にパラグラフブロックを追記
    new_paragraph_text = f" [*] QR情報から商談メモが更新されました: {new_memo}"
    
    url_block = f"https://api.notion.com/v1/blocks/{page_id}/children"
    payload_block = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": new_paragraph_text}
                        }
                    ]
                }
            }
        ]
    }
    resp2 = requests.patch(url_block, headers=headers, json=payload_block)
    resp2.raise_for_status()




# def append_image_blocks(page_id, unique_id, card_image, hearing_images):
#     """
#     作成済みのページ（page_id）の本文に、外部画像URLを用いた画像ブロックを追加する関数です。
#     image_urls は追加する画像のURLのリスト。
#     """
#     url = f"https://api.notion.com/v1/blocks/{page_id}/children"
#     headers = {
#         "Authorization": f"Bearer {NOTION_API_TOKEN}",
#         "Content-Type": "application/json",
#         "Notion-Version": NOTION_VERSION,
#     }
#     children = []
    
#     # 名刺画像の追加
#     card_url = UPLOAD_URL + unique_id + "/card/" + os.path.basename(card_image)
#     children.append({
#         "object": "block",
#         "type": "image",
#         "image": {
#             "type": "external",
#             "external": {"url": card_url}
#         }
#     })
    
#     # ヒアリングシート画像の追加
#     for img_name in hearing_images:

#         img_url = UPLOAD_URL + unique_id + "/hearing/" + os.path.basename(img_name)
#         children.append({
#             "object": "block",
#             "type": "image",
#             "image": {
#                 "type": "external",
#                 "external": {"url": img_url}
#             }
#         })

#     data = {"children": children}
#     response = requests.patch(url, headers=headers, json=data)
#     if response.status_code == 200:
#         print("[*]画像ブロックの追加に成功しました。")
#         return 0
#     else:
#         print(f"画像ブロック追加エラー: {response.text}")

