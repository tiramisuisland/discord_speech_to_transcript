import discord
import os
from yt_dlp import YoutubeDL
import whisper
from opencc import OpenCC
import asyncio
import aiohttp

# ===== Discord 設定 =====
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ===== 音樂下載（YouTube）=====
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
    model = whisper.load_model("small")
    result = model.transcribe(input_filename, language="zh", task="transcribe")

    cc = OpenCC('s2tw')  # 簡體轉台灣繁體

    with open(output_filename, "w", encoding="utf-8") as f:
        for segment in result["segments"]:
            text = cc.convert(segment['text'])
            f.write(f"{text}\n")

    return output_filename

# ===== 指令觸發與檔案處理事件 =====
@client.event
async def on_message(message):
    if message.author.bot:
        return

    # 指令：從 YouTube 下載並轉文字
    if message.content.startswith("!download_YT_to_txt"):
        await message.channel.send("🎬 收到指令，正在處理...請稍候")

        try:
            parts = message.content.split()
            if len(parts) < 2:
                await message.channel.send("❌ 請輸入指令與 YouTube URL，例如：`!download_YT_to_txt https://...`")
                return
            url = parts[1]

            base_name = "yt_audio"
            mp3_file = youtube_download_to_mp3(url, base_name)
            txt_file = base_name + ".txt"

            transcribe_mp3_to_txt(mp3_file, txt_file)

            await message.channel.send(file=discord.File(txt_file))

            os.remove(mp3_file)
            os.remove(txt_file)

        except Exception as e:
            await message.channel.send(f"❌ 發生錯誤：{str(e)}")
            print(f"錯誤詳細：{e}")
        return

    # 處理使用者上傳的音訊檔案
    if message.attachments:
        for attachment in message.attachments:
            filename = attachment.filename.lower()
            if filename.endswith(('.mp3', '.m4a')):
                await message.channel.send("🎧 收到音訊檔，正在下載與轉換中...")

                try:
                    local_audio = "upload_" + filename
                    txt_output = os.path.splitext(local_audio)[0] + ".txt"

                    # 下載檔案
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status == 200:
                                with open(local_audio, 'wb') as f:
                                    f.write(await resp.read())

                    # 語音轉文字
                    transcribe_mp3_to_txt(local_audio, txt_output)

                    # 回傳結果
                    await message.channel.send(file=discord.File(txt_output))

                    # 清理檔案
                    os.remove(local_audio)
                    os.remove(txt_output)

                except Exception as e:
                    await message.channel.send(f"❌ 發生錯誤：{str(e)}")
                    print(f"錯誤詳細：{e}")
            else:
                await message.channel.send("⚠️ 請上傳 mp3 或 m4a 音訊檔案。")

# ===== 啟動 Bot =====
with open("token.txt", "r") as f:
    token = f.read().strip()

client.run(token)
