#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from main import LOGGER as LOGS
from main import Config, Store
import base64
import re
import json
import requests
from bs4 import BeautifulSoup


class ParseLink(object):

    @staticmethod
    def olive(Q, url, path):
        if not re.search(r"https://videos\.sproutvideo\.com/embed/.*/.*", url):
            LOGS.error("Invalid SproutVideo embed URL.")
            return None

        site_link = Store.SPROUT_URL

        try:
            domain_name = re.search(r"http.?://([A-Za-z_0-9.-]+).*", site_link).group(1)
        except Exception as e:
            LOGS.error(f"Domain parse error: {e}")
            return None

        if "https" in site_link:
            referer_link = f"https://{domain_name}/"
        else:
            referer_link = f"http://{domain_name}/"

        headers = {
            "Referer": referer_link,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.41 Safari/537.36"
            ),
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            LOGS.error(f"SproutVideo response error: {response.text}")
            return None

        try:
            response_parts = response.text.split("var dat = '")
            token = response_parts[1].split("'")[0]
        except Exception as e:
            LOGS.error(f"Token parse error: {e}")
            return None

        try:
            token_to_json = json.loads(base64.urlsafe_b64decode(token).decode("UTF-8"))
        except Exception as e:
            LOGS.error(f"Token decode error: {e}")
            return None

        video_name    = token_to_json["title"].replace("/", "").replace(":", "").strip()
        session_id    = token_to_json["sessionID"]
        cdn           = token_to_json["base"]
        sprout_host   = token_to_json["analytics_host"]
        user_hash     = token_to_json["s3_user_hash"]
        video_hash    = token_to_json["s3_video_hash"]

        m3u8_policy     = token_to_json["signatures"]["m"]["CloudFront-Policy"]
        m3u8_signature  = token_to_json["signatures"]["m"]["CloudFront-Signature"]
        m3u8_keypair_id = token_to_json["signatures"]["m"]["CloudFront-Key-Pair-Id"]

        index_link = (
            f"https://{cdn}.{sprout_host}/{user_hash}/{video_hash}/video/index.m3u8"
            f"?Policy={m3u8_policy}&Signature={m3u8_signature}"
            f"&Key-Pair-Id={m3u8_keypair_id}&sessionID={session_id}"
        )

        qualities = requests.get(index_link).text.split("\n")
        Qlty = [i.split(".m3u8")[0] for i in qualities if ".m3u8" in i]
        selected_Q = Q if Q in Qlty else (Qlty[-1] if Qlty else Q)

        Q_link = (
            f"https://{cdn}.{sprout_host}/{user_hash}/{video_hash}/video/{selected_Q}.m3u8"
            f"?Policy={m3u8_policy}&Signature={m3u8_signature}"
            f"&Key-Pair-Id={m3u8_keypair_id}&sessionID={session_id}"
        )
        playlist_contents = requests.get(Q_link).text

        ts_policy     = token_to_json["signatures"]["t"]["CloudFront-Policy"]
        ts_signature  = token_to_json["signatures"]["t"]["CloudFront-Signature"]
        ts_keypair_id = token_to_json["signatures"]["t"]["CloudFront-Key-Pair-Id"]

        ts_parts = re.findall(r".*_.*ts", playlist_contents)
        for ts_part in ts_parts:
            ts_link = (
                f"https://{cdn}.{sprout_host}/{user_hash}/{video_hash}/video/{ts_part}"
                f"?Policy={ts_policy}&Signature={ts_signature}"
                f"&Key-Pair-Id={ts_keypair_id}&sessionID={session_id}"
            )
            playlist_contents = playlist_contents.replace(ts_part, ts_link)

        key_policy     = token_to_json["signatures"]["k"]["CloudFront-Policy"]
        key_signature  = token_to_json["signatures"]["k"]["CloudFront-Signature"]
        key_keypair_id = token_to_json["signatures"]["k"]["CloudFront-Key-Pair-Id"]

        key_link = (
            f"https://{cdn}.{sprout_host}/{user_hash}/{video_hash}/video/{selected_Q}.key"
            f"?Policy={key_policy}&Signature={key_signature}"
            f"&Key-Pair-Id={key_keypair_id}&sessionID={session_id}"
        )
        final_playlist = playlist_contents.replace(f"{selected_Q}.key", key_link)

        file_to_download = f"{path}/{video_name}-{selected_Q}p.m3u8"
        try:
            with open(file_to_download, "w") as m3u8_writer:
                m3u8_writer.write(final_playlist)
        except Exception as e:
            LOGS.error(str(e))
            return None

        return file_to_download

    @staticmethod
    def vision_m3u8_link(link, Q):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "http://www.visionias.in/",
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
            ),
        }
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        paras = soup.find("script")
        url = paras.text.split('"')[3]
        return url

    @staticmethod
    def vision_mpd_link(r_link):
        link = f'http://visionias.in/student/videoplayer_v2/video.php?{r_link.split("?")[-1]}'
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "http://www.visionias.in/",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Mobile Safari/537.36"
            ),
        }
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.content, features="xml")
        res_link1 = soup.find_all("Location")[0].get_text()
        return res_link1

    @staticmethod
    def classplus_link(link):
        headers = {
            "Host": "api.classplusapp.com",
            "x-access-token": Store.CPTOKEN,
            "user-agent": "Mobile-Android",
            "app-version": "1.4.37.1",
            "api-version": "18",
        }
        response = requests.get(
            f"https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={link}",
            headers=headers,
        )
        url = response.json()["url"]
        return url

    @staticmethod
    def is_pw(url):
        r_code = requests.get(url=url)
        if r_code.status_code != 200:
            link = f"https://d3nzo6itypaz07.cloudfront.net/{url.split('/')[3]}/master.m3u8"
            r_code1 = requests.get(url=link)
            if r_code1.status_code == 200:
                return link
            return url
        return url

    @staticmethod
    def topranker_link(url: str):
        host = f"https://{url.split('/')[2]}"
        _id  = url.split("/")[-1].split("-")[0]
        r = requests.post(
            f"{host}/route?route=item%2Fliveclasses&id={_id}"
            "&response-type=2&fromapp=1&loadall=1&clientView=1&liveFromCDN=1&clientVersion=1.9"
        ).json()
        if r["data"]["tr1info"]["primPlaybackUrl"] is None:
            ytid = r["data"]["tr1info"]["data"]["youtubeId"]
            link = f"https://www.youtube.com/watch?v={ytid}"
        else:
            link = r["data"]["tr1info"]["primPlaybackUrl"]
        LOGS.info(link)
        return link

    @staticmethod
    def rout(url, m3u8):
        rout_link = (
            f"https://{url.split('/')[2]}/?route=common/ajax&mod=liveclasses"
            f"&ack=getcustompolicysignedcookiecdn"
            f"&stream={'/'.join(m3u8.split('/')[0:-1]).replace('/', '%2F').replace(':', '%3A')}master.m3u8"
        )
        LOGS.info(rout_link)
        return rout_link

    @staticmethod
    def is_drive_pdf(url):
        if url.startswith("https://drive.google.com/") and any(
            k in url for k in ("file", "open", "sharing", "view", "/d")
        ):
            try:
                _id = url.split("/")[5]
                res = f"https://drive.google.com/uc?export=download&id={_id}"
                LOGS.info(res)
                return res
            except Exception:
                return url
        return url

    @staticmethod
    def cw_url2(class_id):
        ACCOUNT_ID  = "6206459123001"
        BCOV_POLICY = (
            "BCpkADawqM1474MvKwYlMRZNBPoqkJY-UWm7zE1U769d5r5kqTjG0v8L-THXuVZtdIQJpfMPB37L_VJQxTKeNeLO2Eac_"
            "yMywEgyV9GjFDQ2LTiT4FEiHhKAUvdbx9ku6fGnQKSMB8J5uIDd"
        )
        BC_URL = f"https://edge.api.brightcove.com/playback/v1/accounts/{ACCOUNT_ID}/videos"
        BC_HDR = {"BCOV-POLICY": BCOV_POLICY}
        video_response = requests.get(f"{BC_URL}/{class_id}", headers=BC_HDR)
        video = video_response.json()
        try:
            video_url = video["sources"][5]["src"]
        except (IndexError, KeyError):
            video_url = video["sources"][1]["src"]
        return video_url
