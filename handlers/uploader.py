#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import subprocess
import wget
import os
import time
import requests
import asyncio
from helpers.toolkit import Tools, Vidtools
from main import Config, Msg, Store, LOGGER as LOGS
from helpers.prog_bar import progress_for_pyrogram
from pyrogram import Client as AFK
from pyrogram.types import Message


class Upload_to_Tg:
    def __init__(
        self,
        bot: AFK,
        m: Message,
        name: str,
        file_path,
        path,
        Thumb,
        show_msg: Message,
        caption: str,
    ) -> None:
        self.bot       = bot
        self.m         = m
        self.name      = name
        self.file_path = file_path
        self.path      = path
        self.thumb     = Thumb
        self.temp_dir  = f"{path}/{name}"
        self.show_msg  = show_msg
        self.caption   = caption

    async def get_thumb_duration(self):
        try:
            duration = Vidtools.get_duration(self.file_path)
        except Exception:
            try:
                duration = int(Tools.duration(self.file_path))
            except Exception:
                duration = 0

        thumb_str = str(self.thumb) if self.thumb else ""

        if thumb_str.startswith(("http://", "https://")):
            try:
                wget.download(thumb_str, f"{self.temp_dir}.jpg")
                thumbnail = f"{self.temp_dir}.jpg"
            except Exception:
                thumbnail = None
        elif thumb_str and os.path.isfile(thumb_str):
            thumbnail = thumb_str
        else:
            try:
                thumbnail = await Vidtools.take_screen_shot(
                    self.file_path, self.name, self.path, max(duration / 2, 1)
                )
            except Exception:
                try:
                    subprocess.run(
                        f'ffmpeg -i "{self.file_path}" -ss 00:00:01 -vframes 1 "{self.temp_dir}.jpg"',
                        shell=True,
                        check=False,
                    )
                    thumbnail = f"{self.temp_dir}.jpg" if os.path.isfile(f"{self.temp_dir}.jpg") else None
                except Exception:
                    thumbnail = None

        return duration, thumbnail

    async def get_doc_thumb(self):
        thumb_str = str(self.thumb) if self.thumb else ""

        if thumb_str.startswith(("http://", "https://")):
            try:
                wget.download(thumb_str, f"{self.temp_dir}.jpg")
                return f"{self.temp_dir}.jpg"
            except Exception:
                return None
        elif thumb_str and os.path.isfile(thumb_str):
            return thumb_str
        return None

    async def upload_video(self):
        duration, thumbnail = await Upload_to_Tg.get_thumb_duration(self)
        try:
            w, h = await Vidtools.get_width_height(self.file_path)
        except Exception:
            w, h = 1280, 720

        start_time = time.time()
        try:
            await self.bot.send_video(
                chat_id=self.m.chat.id,
                video=self.file_path,
                supports_streaming=True,
                caption=self.caption,
                duration=duration,
                thumb=thumbnail,
                width=w,
                height=h,
                progress=progress_for_pyrogram,
                progress_args=(
                    Msg.CMD_MSG_2.format(file_name=self.name),
                    self.show_msg,
                    start_time,
                ),
            )
        except Exception as e:
            LOGS.error(str(e))
            await self.bot.send_document(
                chat_id=self.m.chat.id,
                document=self.file_path,
                caption=self.caption,
                thumb=thumbnail,
                progress=progress_for_pyrogram,
                progress_args=(
                    Msg.CMD_MSG_2.format(file_name=self.name),
                    self.show_msg,
                    start_time,
                ),
            )

        if os.path.isfile(self.file_path):
            os.remove(self.file_path)
        try:
            await self.show_msg.delete(True)
        except Exception:
            pass

    async def upload_doc(self):
        start_time = time.time()
        doc_thumb  = await Upload_to_Tg.get_doc_thumb(self)
        try:
            await self.bot.send_document(
                chat_id=self.m.chat.id,
                document=self.file_path,
                caption=self.caption,
                thumb=doc_thumb,
                progress=progress_for_pyrogram,
                progress_args=(
                    Msg.CMD_MSG_2.format(file_name=self.name),
                    self.show_msg,
                    start_time,
                ),
            )
        except Exception as e:
            LOGS.error(str(e))

        if os.path.isfile(self.file_path):
            os.remove(self.file_path)
        try:
            await self.show_msg.delete(True)
        except Exception:
            pass
