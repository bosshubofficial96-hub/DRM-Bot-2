import os
import sys
import shutil
import uuid
from pyrogram import filters, Client as AFK
from pyrogram.types import Message
from main import LOGGER as LOGS, prefixes, Config, Msg
from handlers.tg import TgClient, TgHandler
from handlers.downloader import download_handler, get_link_atributes
from handlers.uploader import Upload_to_Tg


@AFK.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("start", prefixes=prefixes)
)
async def start_msg(bot: AFK, m: Message):
    await bot.send_message(chat_id=m.chat.id, text=Msg.START_MSG)


@AFK.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("restart", prefixes=prefixes)
)
async def restart_handler(_, m: Message):
    if os.path.isdir(Config.DOWNLOAD_LOCATION):
        shutil.rmtree(Config.DOWNLOAD_LOCATION)
    await m.reply_text(Msg.RESTART_MSG, True)
    os.execl(sys.executable, sys.executable, *sys.argv)


@AFK.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("pro", prefixes=prefixes)
)
async def Pro(bot: AFK, m: Message):
    session_id = str(uuid.uuid4())[:8]
    sPath = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}/{session_id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/FILE/{m.chat.id}"
    
    error_list = []
    
    os.makedirs(sPath, exist_ok=True)
    BOT = TgClient(bot, m, sPath)

    try:
        nameLinks, num, caption, quality, Token, txt_name, userr = await BOT.Ask_user()
    except Exception as e:
        LOGS.error(str(e))
        await TgHandler.error_message(bot=bot, m=m, error=f"from User Input - {e}")
        await m.reply_text("Wrong Input")
        if os.path.exists(sPath):
            shutil.rmtree(sPath)
        return

    if not nameLinks:
        await m.reply_text("**No links found. Please check your file.**")
        if os.path.exists(sPath):
            shutil.rmtree(sPath)
        return

    try:
        Thumb = await BOT.thumb()
    except Exception as e:
        LOGS.error(str(e))
        Thumb = "no"

    for i in range(num, len(nameLinks)):
        caption_name = ""
        url = ""
        Show = None
        dl_file = None
        
        try:
            name = BOT.parse_name(nameLinks[i][0])
            link = nameLinks[i][1] if len(nameLinks[i]) > 1 else ""
            if not link:
                continue

            wxh = get_link_atributes.get_height_width(link=link, Q=quality)
            caption_name = f"**{str(i+1).zfill(3)}.** - {name} {wxh}"
            file_name = f"{str(i+1).zfill(3)}. - {BOT.short_name(name)} {wxh}"

            Show = await bot.send_message(
                chat_id=m.chat.id,
                text=Msg.SHOW_MSG.format(file_name=file_name, file_link=link),
                disable_web_page_preview=True,
            )

            url = get_link_atributes.input_url(link=link, Q=quality)
            DL = download_handler(name=file_name, url=url, path=sPath, Token=Token, Quality=quality)
            dl_file = await DL.start_download()

            if dl_file and os.path.isfile(dl_file):
                ext = dl_file.rsplit(".", 1)[-1].lower()
                if ext == "mp4":
                    cap = (
                        f"{caption_name}.mp4\n\n"
                        f"<b>𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 : </b>{caption}\n\n"
                        f"<b>𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗯𝘆 ➤ </b> **{userr}**"
                    )
                    UL = Upload_to_Tg(
                        bot=bot, m=m, file_path=dl_file, name=caption_name,
                        Thumb=Thumb, path=sPath, show_msg=Show, caption=cap,
                    )
                    await UL.upload_video()
                else:
                    cap = (
                        f"{caption_name}.{ext}\n\n"
                        f"<b>𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 : </b>{caption}\n\n"
                        f"<b>𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗯𝘆 ➤ </b> **{userr}**"
                    )
                    UL = Upload_to_Tg(
                        bot=bot, m=m, file_path=dl_file, name=caption_name,
                        Thumb=Thumb, path=sPath, show_msg=Show, caption=cap,
                    )
                    await UL.upload_doc()
            else:
                await Show.delete(True)
                error_msg = "File not found after download"
                LOGS.error(f"{error_msg}: {caption_name}")
                if Config.LOG_CH:
                    await bot.send_message(
                        chat_id=Config.LOG_CH,
                        text=Msg.ERROR_MSG.format(
                            error=error_msg,
                            no_of_files=len(error_list),
                            file_name=caption_name,
                            file_link=url,
                        ),
                    )
                error_list.append(f"{caption_name}\n")

        except Exception as r:
            LOGS.error(f"Error processing {caption_name}: {str(r)}")
            if caption_name:
                error_list.append(f"{caption_name}\n")
            
            if Show:
                try:
                    await Show.delete(True)
                except Exception:
                    pass
            
            if Config.LOG_CH:
                try:
                    error_link = url if url else "Unknown URL"
                    await bot.send_message(
                        chat_id=Config.LOG_CH,
                        text=Msg.ERROR_MSG.format(
                            error=str(r),
                            no_of_files=len(error_list),
                            file_name=caption_name if caption_name else f"File_{i+1}",
                            file_link=error_link,
                        ),
                    )
                except Exception as log_err:
                    LOGS.error(f"Failed to send log: {log_err}")
            continue
        
        finally:
            if dl_file and os.path.isfile(dl_file) and 'ext' in locals() and ext != "mp4":
                try:
                    os.remove(dl_file)
                except Exception:
                    pass

    if os.path.exists(sPath):
        try:
            shutil.rmtree(sPath)
        except Exception as e:
            LOGS.error(f"Failed to remove {sPath}: {e}")

    try:
        if os.path.exists(tPath):
            if os.path.isfile(tPath):
                os.remove(tPath)
            elif not os.listdir(tPath):
                shutil.rmtree(tPath)
    except Exception as e1:
        LOGS.error(f"Failed to clean tPath: {e1}")

    try:
        await BOT.linkMsg2(error_list)
    except Exception as e:
        LOGS.error(f"Failed to send error list: {e}")
    
    await m.reply_text("Done ✅")
