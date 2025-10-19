import discord
import re
import os

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TARGET_CHANNEL_ID = int(os.environ.get("TARGET_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def transform_url(message_content):
    # パターン1: https://xcancel.com/(username)/status/(post_id)#m
    match1 = re.search(r'https://xcancel\.com/(\w+)/status/(\d+)(?:#m)?', message_content)
    if match1:
        username = match1.group(1)
        post_id = match1.group(2)
        return f"https://fixupx.com/{username}/{post_id}"
    
    return None

@client.event
async def on_ready():
    print(f'{client.user} としてログインしました')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    new_url = transform_url(message.content)

    if new_url:
        target_channel = client.get_channel(TARGET_CHANNEL_ID)
        if target_channel:
            await target_channel.send(new_url)
        else:
            print(f"エラー: チャンネルID {TARGET_CHANNEL_ID} が見つかりません。")

if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("エラー: Discord Botのトークンが設定されていません。")
