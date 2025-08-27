import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
from moviepy.editor import VideoFileClip

TOKEN = os.getenv("DISCORD_TOKEN")  # Railway stores this safely
MAX_DISCORD_SIZE = 25 * 1024 * 1024  # 25MB limit

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def download_media(url, filename="video.mp4"):
    ydl_opts = {
        "outtmpl": filename,
        "format": "mp4",
        "quiet": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filename


def compress_video(input_file, output_file, target_size=MAX_DISCORD_SIZE):
    clip = VideoFileClip(input_file)
    duration = clip.duration

    target_bitrate = (target_size * 8) / duration
    target_bitrate = max(target_bitrate, 100_000)

    os.system(
        f'ffmpeg -y -i "{input_file}" -b:v {int(target_bitrate)} -bufsize {int(target_bitrate)} "{output_file}"'
    )

    clip.close()
    return output_file


async def process_command(interaction: discord.Interaction, url: str, filename: str):
    await interaction.response.defer()
    try:
        file_path = download_media(url, filename)

        if os.path.getsize(file_path) > MAX_DISCORD_SIZE:
            compressed = "compressed_" + filename
            compress_video(file_path, compressed)
            os.remove(file_path)
            file_path = compressed

        await interaction.followup.send(file=discord.File(file_path))
        os.remove(file_path)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")


@bot.tree.command(name="tiktok", description="Download TikTok video")
async def tiktok(interaction: discord.Interaction, url: str):
    await process_command(interaction, url, "tiktok.mp4")


@bot.tree.command(name="x", description="Download Twitter/X video or photo")
async def x(interaction: discord.Interaction, url: str):
    await process_command(interaction, url, "x.mp4")


bot.run(TOKEN)
