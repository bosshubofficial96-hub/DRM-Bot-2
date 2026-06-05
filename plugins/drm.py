import os
import shutil
from pyrogram import filters, Client as ace
from pyrogram.types import Message
from main import LOGGER, prefixes, Config
from handlers.uploader import Upload_to_Tg
from handlers.tg import TgClient


@ace.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("drm", prefixes=prefixes)
)
async def drm(bot: ace, m: Message):
    path  = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/THUMB/{m.chat.id}"
    os.makedirs(path, exist_ok=True)

    inputData = await bot.ask(m.chat.id, "**Send**\n\nMPD\nNAME\nQUALITY\nCAPTION")
    lines = inputData.text.strip().split("\n")
    if len(lines) < 4:
        await m.reply_text("**Invalid input. Send exactly 4 lines: MPD, NAME, QUALITY, CAPTION**")
        return
    mpd, raw_name, Q, CP = lines[0], lines[1], lines[2], lines[3]
    name = f"{TgClient.parse_name(raw_name)} ({Q}p)"

    inputKeys = await bot.ask(m.chat.id, "**Send Kid:Key (one per line)**")
    keys = " ".join(f"{k.strip()} " for k in inputKeys.text.strip().split("\n") if k.strip())

    BOT   = TgClient(bot, m, path)
    Thumb = await BOT.thumb()
    prog  = await bot.send_message(m.chat.id, f"**Downloading DRM Video!** - [{name}]({mpd})")

    cmd1 = (
        f'yt-dlp -o "{path}/fileName.%(ext)s" '
        f'-f "bestvideo[height<={int(Q)}]+bestaudio" '
        f'--allow-unplayable-format --external-downloader aria2c "{mpd}"'
    )
    os.system(cmd1)

    avDir = os.listdir(path)

    try:
        for data in avDir:
            full = f"{path}/{data}"
            if data.endswith("mp4"):
                os.system(f'mp4decrypt {keys} --show-progress "{full}" "{path}/video.mp4"')
                os.remove(full)
            elif data.endswith("m4a"):
                os.system(f'mp4decrypt {keys} --show-progress "{full}" "{path}/audio.m4a"')
                os.remove(full)

        os.system(
            f'ffmpeg -i "{path}/video.mp4" -i "{path}/audio.m4a" -c copy "{path}/{name}.mp4"'
        )
        for f in ("video.mp4", "audio.m4a"):
            fp = f"{path}/{f}"
            if os.path.isfile(fp):
                os.remove(fp)

        filename = f"{path}/{name}.mp4"
        cc = f"{name}.mp4\n\n**Description:-**\n{CP}"

        UL = Upload_to_Tg(
            bot=bot, m=m, file_path=filename, name=name,
            Thumb=Thumb, path=path, show_msg=prog, caption=cc,
        )
        await UL.upload_video()

    except Exception as e:
        await prog.delete(True)
        await m.reply_text(f"**Error**\n\n`{str(e)}`\n\nOr video may not be available in {Q}p")
    finally:
        if os.path.exists(tPath):
            shutil.rmtree(tPath)
        if os.path.exists(path):
            shutil.rmtree(path)
        await m.reply_text("Done ✅")
