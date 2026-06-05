import os
import shutil
import requests
import wget
import img2pdf
from pyrogram import filters, Client as ace
from pyrogram.types import Message
from main import LOGGER as LOGS, prefixes, Config
from handlers.uploader import Upload_to_Tg
from handlers.tg import TgClient


@ace.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("ytc", prefixes=prefixes)
)
async def ytc_handler(bot: ace, m: Message):
    path  = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/PHOTO/{m.chat.id}"
    os.makedirs(path,  exist_ok=True)
    os.makedirs(tPath, exist_ok=True)

    pages_msg = await bot.ask(m.chat.id, "Send Pages Range Eg: '1:100'\nBook Name\nBookId")
    lines = str(pages_msg.text).strip().split("\n")
    if len(lines) < 3:
        await m.reply_text("**Invalid input. Send 3 lines: PageRange, BookName, BookId**")
        return

    pages, Book_Name, bid = lines[0], lines[1], lines[2]
    page_parts = pages.split(":")
    if len(page_parts) != 2 or not page_parts[0].strip().isdigit() or not page_parts[1].strip().isdigit():
        await m.reply_text("**Invalid page range. Use format: 1:100**")
        return

    page_1    = int(page_parts[0].strip())
    last_page = int(page_parts[1].strip()) + 1

    BASE_URL = (
        "http://yctpublication.com/master/api/MasterController/getPdfPage"
        "?book_id={bid}&page_no={pag}&user_id=14593"
        "&token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjVkZjFmOTQ1ZmY5MDZhZWFlZmE5M2MyNzY5OGRiNDA2ZDYwNmIwZTgiLCJ0eXAiOiJKV1QifQ"
        ".eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyMjkwMDE2MzYyNTQtZWZjcDlqYm4wMzJzbmpmc"
    )

    def download_image(image_link, file_name):
        k = requests.get(url=image_link, timeout=30)
        img_path = f"{tPath}/{file_name}.jpg"
        with open(img_path, "wb") as f:
            f.write(k.content)
        return img_path

    def down(image_link, file_name):
        img_path = f"{tPath}/{file_name}.jpg"
        wget.download(image_link, img_path)
        return img_path

    def downloadPdf(title, imagelist):
        pdf_path = f"{path}/{title}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(imagelist))
        return pdf_path

    Show = await bot.send_message(m.chat.id, "📥 Downloading pages...")
    IMG_LIST = []

    for i in range(page_1, last_page):
        try:
            name = f"{str(i).zfill(3)}_page_{i}"
            y = down(
                image_link=BASE_URL.format(pag=i, bid=bid),
                file_name=name,
            )
            IMG_LIST.append(y)
        except Exception as e:
            LOGS.error(f"Page {i} failed: {e}")
            continue

    if not IMG_LIST:
        await m.reply_text("**No pages downloaded. Check BookId and range.**")
        shutil.rmtree(tPath, ignore_errors=True)
        shutil.rmtree(path, ignore_errors=True)
        return

    try:
        PDF = downloadPdf(title=Book_Name, imagelist=IMG_LIST)
    except Exception as e1:
        await m.reply_text(f"**PDF creation failed:** `{e1}`")
        shutil.rmtree(tPath, ignore_errors=True)
        shutil.rmtree(path, ignore_errors=True)
        return

    UL = Upload_to_Tg(
        bot=bot, m=m, file_path=PDF, name=Book_Name,
        Thumb="no", path=path, show_msg=Show, caption=Book_Name,
    )
    await UL.upload_doc()
    shutil.rmtree(tPath, ignore_errors=True)
    shutil.rmtree(path, ignore_errors=True)
