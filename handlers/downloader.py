import subprocess
from subprocess import getoutput
from handlers.url_scripts import ParseLink
from main import LOGGER as LOGS
import asyncio
import requests
import aiohttp
import aiofiles
import os

cc = 0

EXTRA_LINKS = {
    "CP_VIMEO_TYPE": (
        "https://videos.classplusapp.com/",
        "https://api.edukemy.com/videodetails/",
        "https://tencdn.classplusapp.com",
        "https://covod.testbook.com/",
    ),
    "GUIDELY_LINK": (
        "https://guidely.prepdesk.in/api/",
        "https://ibpsguide.prepdesk.in/api/",
    ),
    "EDU_PDF":    ("https://edukemy-v2-assets.s3.ap-south-1.amazonaws.com/course_content/",),
    "VISION_PDF": (
        "http://www.visionias.in/student/pt/video_student/handout",
        "http://www.visionias.in/student/3.php?",
    ),
}


class get_link_atributes:
    @staticmethod
    def get_wxh(ytdlp):
        try:
            widthXheight = str(getoutput(f"{ytdlp}  -e --get-filename -R 25")).split("\n")[1].strip()
            LOGS.info(widthXheight)
            return widthXheight
        except Exception as e1:
            LOGS.info(str(e1))
            return ".N.A"

    @staticmethod
    def get_height_width(link: str, Q: str):
        url = get_link_atributes.input_url(link=link, Q=Q)
        YTF = f"bv[height<=?{Q}]+ba/[height<=?{Q}]+ba/[height>=?{Q}]+ba/[height<=?{Q}]/[height>=?{Q}]/b"
        if link.endswith("ankul60"):
            url2 = ParseLink.topranker_link(link)
            if "m3u8" in url2:
                rout = ParseLink.rout(url=link, m3u8=url2)
                os.system(f'curl "{rout}" -c "cooks.txt"')
                YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{url2}" --cookies "cooks.txt" -o "%(resolution)s"'
                return get_link_atributes.get_wxh(YTDLP)
            else:
                YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{url2}" --progress -o "%(resolution)s"'
                return get_link_atributes.get_wxh(YTDLP)
        else:
            YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{url}" --progress --remux-video mp4 -o "%(resolution)s"'
            return get_link_atributes.get_wxh(YTDLP)

    @staticmethod
    def input_url(link: str, Q: str):
        if link.startswith("https://videos.classplusapp.com/"):
            if link.split("?")[-1].startswith("auth_key="):
                return link
            return ParseLink.classplus_link(link=link)
        elif link.startswith(("https://vod.visionias.in/player/index.php", "https://vod.visionias.in/player_v2/index.php")):
            return ParseLink.vision_m3u8_link(link, Q)
        elif link.startswith("https://covod.testbook.com/"):
            return ParseLink.classplus_link(link=link)
        elif link.startswith("https://tencdn.classplusapp.com"):
            return ParseLink.classplus_link(link=link)
        elif link.startswith("http://www.visionias.in/student/videoplayer_v2/?"):
            return ParseLink.vision_mpd_link(link)
        elif link.startswith("https://d1d34p8vz63oiq.cloudfront.net/"):
            return ParseLink.is_pw(link)
        elif "drive" in link:
            return ParseLink.is_drive_pdf(url=link)
        elif link.startswith("https://videotest.adda247.com/"):
            if link.split("/")[3] != "demo":
                return f'https://videotest.adda247.com/demo/{link.split("https://videotest.adda247.com/")[1]}'
            return link
        elif not link.startswith("http"):
            parts = link.split("*", 1)
            return ParseLink.cw_url2(parts[0]) + (parts[1] if len(parts) > 1 else "")
        return link


class Download_Methods:
    def __init__(self, name: str, url: str, path, Token: str, Quality: str) -> None:
        self.url      = url
        self.name     = name
        self.Q        = Quality
        self.path     = path
        self.token    = Token
        self.temp_dir = f"{path}/{name}"

    async def m3u82mp4(self, file):
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
                "-i", file, "-c", "copy", "-bsf:a", "aac_adtstoasc",
                f"{self.temp_dir}.mp4",
            ]
        )
        if os.path.isfile(file):
            os.remove(file)
        if os.path.isfile(f"{self.temp_dir}.mp4"):
            return f"{self.temp_dir}.mp4"
        return None

    def addapdf(self):
        cookies = {"cp_token": self.token}
        headers = {
            "Host": "store.adda247.com",
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 11; moto g(40) fusion Build/RRI31.Q1-42-51-8; wv) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/97.0.4692.98 Mobile Safari/537.36"
            ),
            "accept": "*/*",
            "x-requested-with": "com.adda247.app",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://store.adda247.com/build/pdf.worker.js",
            "accept-language": "en-US,en;q=0.9",
        }
        response = requests.get(self.url, cookies=cookies, headers=headers)
        with open(f"{self.temp_dir}.pdf", "wb") as f:
            f.write(response.content)
        return f"{self.temp_dir}.pdf"

    async def aio(self):
        k = f"{self.temp_dir}.pdf"
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(k, mode="wb") as f:
                        await f.write(await resp.read())
        return k

    def cwpdf(self):
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; Redmi Note 5 Pro MIUI/V11.0.5.0.PEIMIXM)",
            "Host": "elearn.crwilladmin.com",
            "Connection": "Keep-Alive",
        }
        r_pdf = requests.get(self.url, headers=headers)
        with open(f"{self.temp_dir}.pdf", "wb") as f:
            f.write(r_pdf.content)
        pdf = f"{self.temp_dir}.pdf"
        return pdf if os.path.isfile(pdf) else None

    def visionpdf(self):
        cookies = {"PHPSESSID": self.token}
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
            ),
        }
        response = requests.get(self.url, cookies=cookies, headers=headers, verify=False)
        with open(f"{self.temp_dir}.pdf", "wb") as f:
            f.write(response.content)
        return f"{self.temp_dir}.pdf" if os.path.isfile(f"{self.temp_dir}.pdf") else None

    async def Guidely(self):
        data = requests.get(self.url).json()
        z   = data["item"]["data"]["key"]
        mpd = data["item"]["data"]["file"]
        LOGS.info(f"Guidely key={z}  mpd={mpd}")
        cmd1 = (
            f'yt-dlp -o "{self.path}/Name.%(ext)s" -f "bestvideo[height<={self.Q}]+bestaudio" '
            f'--allow-unplayable-format --external-downloader aria2c "{mpd}"'
        )
        os.system(cmd1)
        for d in os.listdir(self.path):
            if d.endswith("mp4"):
                os.system(f'mp4decrypt --key 1:{z} "{self.path}/{d}" "{self.path}/video.mp4"')
                os.remove(f"{self.path}/{d}")
            elif d.endswith("m4a"):
                os.system(f'mp4decrypt --key 1:{z} "{self.path}/{d}" "{self.path}/audio.m4a"')
                os.remove(f"{self.path}/{d}")
        os.system(
            f'ffmpeg -i "{self.path}/video.mp4" -i "{self.path}/audio.m4a" -c copy "{self.temp_dir}.mp4"'
        )
        for leftover in ("video.mp4", "audio.m4a"):
            fp = f"{self.path}/{leftover}"
            if os.path.isfile(fp):
                os.remove(fp)
        return f"{self.temp_dir}.mp4" if os.path.isfile(f"{self.temp_dir}.mp4") else None

    def get_drive_link_type(self):
        try:
            c_type = requests.get(self.url).headers["Content-Type"].lower()
            return c_type
        except Exception as e2:
            LOGS.error(str(e2))
            return None

    def dot_ws_link(self):
        response = requests.get(self.url, stream=True)
        LOGS.info(response.status_code)
        with open(f"{self.temp_dir}.html", "wb") as f:
            f.write(response.content)
        return f"{self.temp_dir}.html" if os.path.isfile(f"{self.temp_dir}.html") else None


class download_handler(Download_Methods):
    def run_cmd(self, cmd):
        LOGS.info(cmd)
        try:
            subprocess.run(cmd, shell=True)
        except Exception as e_:
            LOGS.info(str(e_))
        file_path = f"{self.temp_dir}.mp4"
        return file_path

    def recursive(self, cmd):
        LOGS.info(cmd)
        global cc
        if cc >= 5:
            cc = 0
            return f"{self.temp_dir}.mp4"
        dl = subprocess.run(cmd, shell=True)
        if dl.returncode != 0:
            cc += 1
            return download_handler.recursive(self, cmd=cmd)
        cc = 0
        file_path = f"{self.temp_dir}.mp4"
        LOGS.info(str(file_path))
        return file_path

    async def recursive_asyno(self, cmd):
        LOGS.info(cmd)
        global cc
        if cc >= 5:
            cc = 0
            return f"{self.temp_dir}.mp4"
        process = await asyncio.create_subprocess_shell(
            cmd=cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        print(f"Started: (pid={process.pid})", flush=True)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            cc += 1
            return await download_handler.recursive_asyno(self, cmd=cmd)
        cc = 0
        print(f"Done: (pid={process.pid})", flush=True)
        file_path = f"{self.temp_dir}.mp4"
        LOGS.info(str(file_path))
        return file_path

    async def start_download(self):
        YTF = f"bv[height<=?{self.Q}]+ba/[height<=?{self.Q}]+ba/[height>=?{self.Q}]+ba/[height<=?{self.Q}]/[height>=?{self.Q}]/b"
        YTDLP = (
            f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{self.url}" '
            f'--merge-output-format mp4 --remux-video mp4 -o "{self.temp_dir}.%(ext)s"'
        )
        CMD = (
            f"{YTDLP} -R 25 --fragment-retries 25 "
            f"--external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
        )

        if self.url.startswith("https://elearn.crwilladmin.com/") and self.url.endswith(".pdf"):
            return download_handler.cwpdf(self)

        if (
            self.url.endswith(".pdf")
            or ".pdf" in self.url
            or self.url.startswith(EXTRA_LINKS["EDU_PDF"])
        ):
            return await download_handler.aio(self)

        if self.url.startswith("https://store.adda247.com/"):
            return download_handler.addapdf(self)

        if self.url.startswith(EXTRA_LINKS["VISION_PDF"]):
            return download_handler.visionpdf(self)

        if self.url.startswith(EXTRA_LINKS["GUIDELY_LINK"]):
            return await download_handler.Guidely(self)

        if self.url.startswith("https://videos.sproutvideo.com/"):
            file = ParseLink.olive(self.Q, self.url, self.path)
            if file:
                return await download_handler.m3u82mp4(self, file)
            return None

        if "drive" in self.url:
            c_type = download_handler.get_drive_link_type(self)
            if c_type and "pdf" in c_type:
                return await download_handler.aio(self)
            if c_type and "video" in c_type:
                return await download_handler.recursive_asyno(self, cmd=CMD)
            return await download_handler.aio(self)

        if self.url.endswith("ankul60"):
            m3u8url = ParseLink.topranker_link(self.url)
            if "m3u8" in m3u8url:
                rout = ParseLink.rout(url=self.url, m3u8=m3u8url)
                os.system(f'curl "{rout}" -c "cooks.txt"')
                YTDLP2 = (
                    f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{m3u8url}" '
                    f'--cookies "cooks.txt" --remux-video mp4 -o "{self.temp_dir}.%(ext)s"'
                )
                CMD2 = (
                    f"{YTDLP2} -R 25 --fragment-retries 25 "
                    f"--external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
                )
                file_name = await download_handler.recursive_asyno(self, cmd=CMD2)
                if os.path.isfile("cooks.txt"):
                    os.remove("cooks.txt")
                return file_name
            else:
                self.url = m3u8url
                return await download_handler.recursive_asyno(self, cmd=CMD)

        if self.url.endswith(".ws"):
            return download_handler.dot_ws_link(self)

        return download_handler.recursive(self, cmd=CMD)
