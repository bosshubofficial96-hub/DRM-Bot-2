from bs4 import BeautifulSoup
import os


def parse_html(file):
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    soup = BeautifulSoup(source, "html.parser")

    info     = soup.select_one("p#info")
    mg_info  = soup.select_one("p[style='text-align:center;font-size:30;color:Blue']")
    buttons_soup = soup.select("button.collapsible")
    paras_soup   = soup.select("p")[2:]

    def is_valid_url(u):
        return u and (u.startswith("http://") or u.startswith("https://"))

    videos = []

    if info is not None:
        all_videos_soup = soup.select_one("div#videos")
        if all_videos_soup:
            topics_soup = all_videos_soup.select("div.topic")
            for topic_soup in topics_soup:
                videos_soup = topic_soup.select("p.video")
                for video_soup in videos_soup:
                    video_name = video_soup.select_one("span.video_name")
                    a_tag      = video_soup.select_one("a")
                    if not video_name or not a_tag:
                        continue
                    video_link = a_tag.get_text(strip=True)
                    if not is_valid_url(video_link):
                        continue
                    videos.append(
                        f"{video_name.get_text(strip=True).replace(':', '')}:{video_link}".split(":", 1)
                    )

    elif mg_info is not None and buttons_soup:
        for button_soup in buttons_soup:
            content_div = button_soup.find_next_sibling("div", class_="content")
            if not content_div:
                continue
            para = content_div.p
            if not para:
                continue
            for a_soup in para.select("a"):
                br = a_soup.find_previous_sibling()
                if br:
                    br.decompose()
                video_name = a_soup.previousSibling
                video_link = a_soup.get_text(strip=True)
                if not is_valid_url(video_link):
                    continue
                name_str = str(video_name).replace(":", "") if video_name else ""
                videos.append(f"{name_str}:{video_link}".split(":", 1))

    elif mg_info is not None and paras_soup and paras_soup[0].b is not None:
        for i, topic_para in enumerate(paras_soup):
            if i % 2 != 0:
                continue
            para = topic_para.find_next_sibling("p")
            if not para:
                continue
            for a_soup in para.select("a"):
                br = a_soup.find_previous_sibling()
                if br:
                    br.decompose()
                video_name = a_soup.previousSibling
                video_link = a_soup.get_text(strip=True)
                if not is_valid_url(video_link):
                    continue
                name_str = str(video_name).replace(":", "") if video_name else ""
                videos.append(f"{name_str}:{video_link}".split(":", 1))

    elif (
        mg_info is not None
        and paras_soup
        and paras_soup[0].get("style") == "text-align:center;font-size:25px;"
    ):
        for para in paras_soup:
            a_tag = para.select_one("a")
            if not a_tag:
                continue
            video_link = a_tag.get_text(strip=True)
            if not is_valid_url(video_link):
                continue
            video_name = para.contents[0] if para.contents else ""
            name_str   = str(video_name).replace(":", "")
            videos.append(f"{name_str}:{video_link}".split(":", 1))

    else:
        for a_soup in soup.select("a"):
            video_link = a_soup.get("href") or ""
            if not is_valid_url(video_link):
                continue
            videos.append(f":{video_link}".split(":", 1))

    return videos
