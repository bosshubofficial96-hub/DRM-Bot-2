#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import time


async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if diff == 0:
        return
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_ms = round(diff) * 1000
        eta_ms = round((total - current) / speed) * 1000 if speed else 0
        total_ms = elapsed_ms + eta_ms

        elapsed_str = TimeFormatter(milliseconds=elapsed_ms)
        total_str = TimeFormatter(milliseconds=total_ms)

        bar = "[{0}{1}] \n**P:** {2}%\n".format(
            "▪️" * math.floor(percentage / 10),
            "▫️" * (10 - math.floor(percentage / 10)),
            round(percentage, 2),
        )
        tmp = bar + "**Size:** {0} of {1}\n**Speed:** {2}/s\n**ETA:** {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            total_str if total_str else "0 s",
        )
        try:
            await message.edit(text=f"{ud_type}\n\n{tmp}")
        except Exception:
            pass


def humanbytes(size):
    if not size:
        return ""
    power = 2 ** 10
    n = 0
    labels = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {labels[n]}B"


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        (f"{days}d, " if days else "") +
        (f"{hours}h, " if hours else "") +
        (f"{minutes}m, " if minutes else "") +
        (f"{seconds}s, " if seconds else "") +
        (f"{milliseconds}ms, " if milliseconds else "")
    )
    return tmp[:-2] if tmp else ""
