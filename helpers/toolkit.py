#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import datetime
import asyncio
import wget
import requests
import time
import aiohttp
import aiofiles
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from main import Config


class Tools(object):
    @staticmethod
    def duration(filename):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        return float(result.stdout)

    @staticmethod
    async def aio(url, name, path):
        k = f"{path}/{name}.pdf"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(k, mode="wb") as f:
                        await f.write(await resp.read())
        return k

    @staticmethod
    def human_readable_size(size, decimal_places=2):
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024.0 or unit == "PB":
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f} {unit}"

    @staticmethod
    def time_name():
        date = datetime.date.today()
        now  = datetime.datetime.now()
        return f"📅 **Date** ~ `{date}`\n🕰 **Time** ~ `{now.strftime('%H : %M : %S')}`"

    @staticmethod
    def convert(seconds):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    @staticmethod
    async def pdf_thumb(Thumb, name, path):
        if Thumb and Thumb.startswith(("http://", "https://")):
            wget.download(Thumb, f"{path}/{name}.jpg")
        else:
            wget.download(
                "https://telegra.ph/file/84870d6d89b893e59c5f0.jpg",
                f"{path}/{name}.jpg",
            )
        return f"{path}/{name}.jpg"


class Vidtools(object):
    @staticmethod
    async def take_screen_shot(video_file, name, path, ttl):
        out_put = f"{path}/{name}.jpg"
        if video_file.upper().endswith(("MKV", "MP4", "WEBM")):
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-ss", str(ttl), "-i", video_file, "-vframes", "1", out_put,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
        return out_put if os.path.lexists(out_put) else None

    @staticmethod
    def get_duration(filepath):
        metadata = extractMetadata(createParser(filepath))
        if metadata and metadata.has("duration"):
            return metadata.get("duration").seconds
        return 0

    @staticmethod
    async def get_width_height(filepath):
        metadata = extractMetadata(createParser(filepath))
        if metadata and metadata.has("width") and metadata.has("height"):
            return metadata.get("width"), metadata.get("height")
        return 1280, 720
