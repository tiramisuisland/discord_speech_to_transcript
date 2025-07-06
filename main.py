import discord
import os
from yt_dlp import YoutubeDL
import whisper
from opencc import OpenCC
import asyncio

# ===== Discord 設定 =====
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ===== 音樂下載 =====
def youtube_download_to_mp3(url, output_filename):
    output_filename, _ = os.path.splitext(output_filename)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename + '.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'retries': 3,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
        ],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_filename + ".mp3"

# ===== Whisper 語音辨識 + OpenCC 繁體轉換 =====
def transcribe_mp3_to_txt(input_filename, output_filename):
    model = whisper.load_model("medium")
    result = model.transcribe(input_filename, language="zh", task="transcribe")

    cc = OpenCC('s2tw')  # 簡體轉繁體

    with open(output_filename, "w", encoding="utf-8") as f:
        for segment in result["segments"]:
            text = cc.convert(segment['text'])
            f.write(f"{text}\n")

    return output_filename

# ===== 指令觸發事件 =====
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!download_YT_to_txt"):
        await message.channel.send("🎬 收到指令，正在處理...請稍候")

        try:
            # 解析指令與 URL
            parts = message.content.split()
            if len(parts) < 2:
                await message.channel.send("❌ 請輸入指令與 YouTube URL，例如：`!download_YT_to_txt https://...`")
                return
            url = parts[1]

            # 設定檔案名稱（簡單處理）
            base_name = "yt_audio"
            mp3_file = youtube_download_to_mp3(url, base_name)
            txt_file = base_name + ".txt"

            # 語音轉文字
            transcribe_mp3_to_txt(mp3_file, txt_file)

            # 回傳文字檔
            await message.channel.send(file=discord.File(txt_file))

            # 清理檔案（可選）
            os.remove(mp3_file)
            os.remove(txt_file)

        except Exception as e:
            await message.channel.send(f"❌ 發生錯誤：{str(e)}")
            print(f"錯誤詳細：{e}")

# ⚠️ 請將 YOUR_DISCORD_BOT_TOKEN 換成你的實際 token
client.run("")

