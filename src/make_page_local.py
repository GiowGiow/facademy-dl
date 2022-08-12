import sys
from asyncio import run
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup
from tqdm import tqdm

from downloader import Downloader
from misc import set_logging_handlers

logger = set_logging_handlers("make_page_local.log")


def remove_google_analytics(soup):
    for noscript in soup("noscript"):
        noscript.extract()


def remove_video(soup):
    video = soup.find("div", {"class": "video"})
    video.extract()


def remove_telemetry(soup):
    remove_google_analytics(soup)
    for s in soup.select('div[class*="octa"]'):
        s.extract()
    remove_telemetry_scripts(soup)


# Remove telemetry
def remove_telemetry_scripts(soup):
    for script in soup("noscript"):
        script.extract()

    scripts = soup(["script", "a", "input", "meta"])
    block_words = [
        "user",
        "analyt",
        "google",
        "octa",
        "chat",
        "survey",
        "track",
        "metric",
        "token",
    ]
    for script in scripts:
        script_as_str = str(script).lower()
        if any(substring in script_as_str for substring in block_words):
            script.decompose()


def remove_user_area(soup):
    user_area = soup.find("div", {"class": "social_area"})
    if user_area:
        user_area.decompose()


def remove_after_video(soup):
    video_after = soup.find("div", {"class": "btn_vid_after"})
    if video_after:
        video_after.decompose()


def remove_audio_js(soup):
    audio_js = soup.find("div", {"class": "post-audio"})
    if audio_js:
        audio_js.decompose()


def remove_unit_downloads(soup):
    unit_downloads = soup.find("div", {"class": "sidebar"})
    if unit_downloads:
        unit_downloads.decompose()


def remove_survey(soup):
    survey = soup.find("div", {"id": "survicate-box"})
    if survey:
        survey.decompose()


def remove_add_to_deck(soup):
    deck = soup.find("a", {"class": "add_deck"})
    if deck:
        deck.decompose()


def remove_broken_img(soup):
    imgs = soup.find_all("img", {"src": "img/img"})
    for img in imgs:
        img.decompose()


def remove_walk_and_talk(soup):
    body = soup.find_all("body", {"class": "containEmbed"})
    if not body:
        return False
    for b in body:
        b.decompose()


def remove_mail_from_html(soup):
    mails = soup.find_all("input", {"id": "assessment_result_email"})
    if not mails:
        return
    for mail in mails:
        mail.decompose()


def create_folder_asset(path, url):
    url_parsed = urlparse(url)
    file_path = path / unquote(Path(url_parsed.path).name)
    # Create folder for assets
    path.mkdir(parents=True, exist_ok=True)
    return file_path


def replace_asset(soup_tag, attr, new_attr_value):
    if soup_tag.has_attr(attr):
        soup_tag[attr] = new_attr_value
        return True
    else:
        print(f"No attr {attr} in soup tag {soup_tag}")
        return None


def fix_link(url):
    if "https:" not in url:
        url = "https:" + url
    return url


def make_assets_local(
    soup,
    html_path,
    tag_to_look_for,
    link_attr,
    asset_type,
    decompose,
    attr_to_look_for=None,
):
    tags = []
    if attr_to_look_for:
        tags = soup.find_all(tag_to_look_for, attr_to_look_for)
    else:
        tags = soup.find_all(tag_to_look_for)

    download_list = set()

    for tag in tags:
        if tag.has_attr(link_attr):
            if tag[link_attr].startswith("data:image"):
                continue
            if tag[link_attr].strip() == "":
                continue
            url = fix_link(tag[link_attr])
            asset_folder = Path(html_path).parent / asset_type
            file_path = create_folder_asset(asset_folder, url)
            # Add to download list
            download_list.add((url, file_path))
            # Replace on HTML
            file_path = Path(asset_type) / Path(file_path).name
            replace_asset(tag, link_attr, file_path)
        else:
            if decompose:
                tag.decompose()
    tries = 3
    for attempt in range(tries):
        try:
            downloader = Downloader()
            run(downloader.download_list_of_files(download_list))
        except Exception as e:
            logger.error(f"Error downloading {download_list} {e}")
            logger.error(f"Attempt {attempt}")
            if attempt < tries - 1:
                continue
        break


def append_new_video(soup, new_video):
    if not new_video:
        return False

    old_video = soup.find("div", {"class": "video"})
    if old_video:
        parent = old_video.parent
        if not parent:
            return False
        video_html = f"""
    <video width="100%" height="auto" controls>
    <source src="{new_video}" type="video/mp4">
    </video>
    """
        parent.append(BeautifulSoup(video_html, "html.parser"))
        old_video.decompose()
        return True

    return False


def find_mp4_video(path):
    for mp4_file in Path(path).parent.glob("*.mp4"):
        return mp4_file.name
    return None


def filter_and_download_page(abs_path):
    with open(abs_path, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    remove_telemetry(soup)
    remove_user_area(soup)
    remove_after_video(soup)
    remove_audio_js(soup)
    remove_unit_downloads(soup)
    remove_survey(soup)
    remove_add_to_deck(soup)
    remove_walk_and_talk(soup)
    remove_mail_from_html(soup)

    make_assets_local(
        soup,
        html_path=abs_path,
        tag_to_look_for="link",
        attr_to_look_for={"rel": "stylesheet"},
        link_attr="href",
        asset_type="css",
        decompose=False,
    )
    # Only download scripts when needed (for assessments)
    if "assessment" in str(abs_path):
        make_assets_local(
            soup,
            html_path=abs_path,
            tag_to_look_for="script",
            link_attr="src",
            asset_type="js",
            decompose=True,
        )
    else:
        # If not needed, remove the script tags from html
        scripts = soup("script")
        for script in scripts:
            script.decompose()

    make_assets_local(
        soup,
        html_path=abs_path,
        tag_to_look_for="img",
        link_attr="src",
        asset_type="img",
        decompose=True,
    )

    append_new_video(soup, find_mp4_video(abs_path))

    assessment_path = Path(abs_path).parent / "assessment"
    if assessment_path.exists():
        iframe = soup.find("iframe")
        if iframe:
            if iframe.has_attr("src"):
                iframe["src"] = "assessment/assessment_page-giow.html"
                iframe["style"] = "height: 550px"

    font_file = Path(abs_path).parent / "css" / "font-awesome.min.css"
    if font_file.exists():
        with font_file.open("r+") as f:
            content = f.read()
            content = content.replace(
                "../fonts/",
                "https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/",
            )
            f.seek(0)
            f.write(content)
            f.truncate()

    remove_broken_img(soup)
    abs_path = Path(abs_path)
    new_name = abs_path.stem + "-giow" + abs_path.suffix

    with open(abs_path.parent / new_name, "w") as f:
        f.write(str(soup))


def get_all_custom_html_files(project_path):
    html_paths = list(Path(project_path).glob("**/*.html"))
    html_paths = [
        html_path
        for html_path in html_paths
        if "-giow" not in str(html_path)  # ignore custom made html files
    ]
    return html_paths


def download_assets_and_edit_htmls(project_path):
    html_paths = get_all_custom_html_files(project_path)
    for html_path in tqdm(html_paths):
        filter_and_download_page(html_path)


if __name__ == "__main__":

    if len(sys.argv) == 2:
        project_path = sys.argv[1]
        download_assets_and_edit_htmls(project_path)
