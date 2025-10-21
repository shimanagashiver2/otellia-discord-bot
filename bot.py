import discord
import re
import os
from flask import Flask
from threading import Thread

# --- Flask Web Server (RenderのKeep-Alive用) ---
# この部分がWebサーバーとして機能し、UptimeRobotからのアクセスに応答します
app = Flask('')

@app.route('/')
def home():
    # UptimeRobotがアクセスした時に、このテキストが返されます
    return "Bot is alive!"

def run_flask():
    # Renderが指定するポートで、外部からのアクセスを待つように設定
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_keep_alive_thread():
    # Botの実行と同時に、このWebサーバーを別スレッドで起動します
    t = Thread(target=run_flask)
    t.daemon = True # メインのBotが終了したら、こちらも終了する
    t.start()

# --- ここから下は、以前作成したDiscord Botのコード ---

# 環境変数からトークンとIDを取得
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TARGET_CHANNEL_ID_STR = os.environ.get("TARGET_CHANNEL_ID")
TARGET_CHANNEL_ID = 0 # 初期化

# チャンネルIDが正しく読み込まれたかチェック
if TARGET_CHANNEL_ID_STR:
    try:
        TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_STR)
    except ValueError:
        print("エラー: TARGET_CHANNEL_ID が整数ではありません。")
else:
    print("エラー: TARGET_CHANNEL_ID が設定されていません。")


# Botの基本的な設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def transform_url(message_content):
    """
    メッセージ内容から特定のURLを抽出し、fixupx.comの形式に変換する関数
    """
    # パターン1: 新しい nitter.aishiteiru.moe のURLを検出
    match1 = re.search(r'https://nitter\.aishiteiru\.moe/(\w+)/status/(\d+)', message_content)
    if match1:
        username = match1.group(1)
        post_id = match1.group(2)
        return f"https://fixupx.com/{username}/status/{post_id}"

    # パターン2: 以前の xcancel.com のURLも検出 (念のため残しておきます)
    match2 = re.search(r'https://xcancel\.com/(\w+)/status/(\d+)', message_content)
    if match2:
        username = match2.group(1)
        post_id = match2.group(2)
        return f"https://fixupx.com/{username}/status/{post_id}"

    # (念のため) RSSフィードのURL自体を検出するパターン
    match_rss_nitter = re.search(r'https://nitter\.aishiteiru\.moe/(\w+)/rss', message_content)
    if match_rss_nitter:
        username = match_rss_nitter.group(1)
        return f"（変換元RSS: https://fixupx.com/{username}）"

    match_rss_xcancel = re.search(r'https://rss\.xcancel\.com/(\w+)/rss', message_content)
    if match_rss_xcancel:
        username = match_rss_xcancel.group(1)
        return f"（変換元RSS: https://fixupx.com/{username}）"

    return None
    
@client.event
async def on_ready():
    """
    Botが正常に起動した際に実行される関数
    """
    print(f'{client.user} としてログインしました')
    print(f'ターゲットチャンネルID: {TARGET_CHANNEL_ID}')

@client.event
async def on_message(message):
    """
    メッセージが投稿された際に実行される関数
    """
    # Bot自身のメッセージは無視する
    if message.author == client.user:
        return

    # URLを変換
    new_url = transform_url(message.content)

    if new_url:
        # ターゲットチャンネルを取得
        target_channel = client.get_channel(TARGET_CHANNEL_ID)
        if target_channel:
            # 変換後のURLを投稿
            try:
                await target_channel.send(new_url)
            except discord.Forbidden:
                print(f"エラー: チャンネル {TARGET_CHANNEL_ID} への投稿権限がありません。")
            except Exception as e:
                print(f"エラー: メッセージ送信中に問題が発生しました - {e}")
        else:
            print(f"エラー: チャンネルID {TARGET_CHANNEL_ID} が見つかりません。")

# --- BotとWebサーバーを起動 ---
if __name__ == "__main__":
    if not DISCORD_TOKEN or TARGET_CHANNEL_ID == 0:
        print("エラー: DISCORD_TOKEN または TARGET_CHANNEL_ID が環境変数に正しく設定されていません。")
    else:
        # 1. Keep-Alive用のWebサーバーを起動
        start_keep_alive_thread()
        print("Keep-Alive Webサーバーを起動しました。")
        
        # 2. Discord Botを起動 (これがメインの処理になります)
        print("Discord Botを起動します...")
        client.run(DISCORD_TOKEN)

