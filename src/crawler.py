from asyncio import run
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from tqdm import tqdm

from downloader import Downloader
from misc import (
    file_path,
    load_queue,
    load_visited_links,
    sanitize_string,
    save_queue,
    save_visited_links,
    set_logging_handlers,
)
from page_loader import PageLoader
from page_parser import PageParser

logger = set_logging_handlers("logs.log")


def get_queue(parser, modules_to_crawl):
    print("Getting queue...")
    # Generate and save the queue if it doesnt exist
    modules_queue = "modules_queue.pkl"
    print(file_path(modules_queue))
    if not Path(file_path(modules_queue)).exists():
        print("Generating queue...")
        queue = generate_queue(parser, modules_to_crawl)
        save_queue(queue, modules_queue)
        visited_links = set(["https://cursos.fluencyacademy.io/"])
        save_visited_links(visited_links, "visited_links.pkl")
        return queue, visited_links
    # Load previously created queue
    else:
        print("Loading previously created queue...")
        queue = load_queue(modules_queue)
        visited_links = load_visited_links("visited_links.pkl")
        return queue, visited_links


def generate_queue(parser, modules_to_crawl):
    queue = deque()
    links_to_visit = set()
    links_to_visit.add(
        "https://cursos.fluencyacademy.io/"
    )  # Ignore the base website

    modules = parser.get_modules()

    # Generate List of Links from the Modules to Crawl
    for name in modules_to_crawl:
        if name not in modules:
            print(f"Module {name} not in page...")
            continue
        print(f"Getting links for module: {name}")
        # Do not add repeated links

        if "link" in modules[name]:
            if modules[name]["link"] not in links_to_visit:
                links_to_visit.add(modules[name]["link"])
                queue.append(modules[name]["link"])

        # If the module does not have any submodule, ignore
        if "submodules" not in modules[name]:
            continue

        # Add submodules to the queue as well
        for submodule in modules[name]["submodules"]:
            link = modules[name]["submodules"][submodule]["link"]
            if link not in links_to_visit:
                links_to_visit.add(link)
                queue.append(link)

    return queue


def enumerate_path_to_save(lesson_count, path):
    # Enumerate folder to save
    path = path.split("/")
    path[-1] = f"{lesson_count}. " + path[-1]
    path = "/".join(path)
    return Path(path)


def crawl(queue, visited_links):
    """First load the first page in the module, parse it, follow links in the left bar"""
    print("Crawling...")
    while tqdm(queue):
        module_to_crawl = queue[0]  # do not pop yet
        page_loader = PageLoader()
        # Load Page
        print("Loading first page to get the submodules...")
        page_html = page_loader.load_page(module_to_crawl)
        if not page_html:
            logger.warning(f"Request to page failed: {module_to_crawl}")
            break

        parser = PageParser(page_html)
        if not parser:
            logger.warning(f"Could not parse page: {page_html}")
            break

        # Extract info
        title = sanitize_string(parser.get_lesson_title())
        path = sanitize_string(parser.get_lesson_path())
        files = parser.find_post_downloads()
        video_url = parser.find_video()
        assessment = parser.find_assessment()

        _, section_lessons = parser.find_section_lessons()

        lesson_count = 1
        path = enumerate_path_to_save(lesson_count, path)
        show_lesson_info(title, path, files, video_url, assessment)

        # Save page
        create_lesson_path(path)
        save_page_html(page_loader, title, path)
        save_screenshot(page_loader, title, path)
        download_video(title, path, video_url)
        download_files(path, files)
        download_assessment(page_loader, path, assessment)

        # 1: is to ignore the first one that we crawled
        for lesson_url in tqdm(section_lessons[1:]):
            if lesson_url in visited_links:
                lesson_count += 1
                print(f"Skipping already visited link {lesson_url}")
                continue

            lesson_html = page_loader.load_page(lesson_url)
            if not lesson_html:
                logger.warning(f"Request to page failed: {module_to_crawl}")
                continue

            parser = PageParser(lesson_html)
            if not parser:
                logger.warning(f"Could not parse page: {lesson_html}")
                continue

            title = sanitize_string(parser.get_lesson_title())
            path = sanitize_string(parser.get_lesson_path())
            files = parser.find_post_downloads()
            video_url = parser.find_video()
            assessment = parser.find_assessment()

            lesson_count += 1
            path = enumerate_path_to_save(lesson_count, path)

            show_lesson_info(title, path, files, video_url, assessment)
            create_lesson_path(path)
            save_page_html(page_loader, title, path)
            save_screenshot(page_loader, title, path)

            download_video(title, path, video_url)
            download_files(path, files)
            download_assessment(page_loader, path, assessment)

            # Save the state
            visited_links.add(lesson_url)
            save_visited_links(visited_links, "visited_links.pkl")

        # Kill our pageloader so it doesnt use too much RAM
        page_loader.driver.close()
        page_loader.driver.quit()

        # Finally pop module url from the queue
        visited_links.add(queue.popleft())

        # Save the state
        save_queue(queue, "modules_queue.pkl")
        save_visited_links(visited_links, "visited_links.pkl")


def download_assessment(page_loader, path, assessment):
    if assessment:
        print(f"Downloading Assessment: {path}")
        try:
            print("Loading Assessment Page...")
            page_loader.driver.get(assessment)
            assess_path = path / "assessment"
            assess_path.mkdir(parents=True, exist_ok=True)
            page_loader.save_html(assess_path / "assessment_page")
        except Exception as e:
            logger.warning(f"Download failed for assessment: {assessment}")
            logger.warning(f"Error: {str(e)}")


def download_files(path, files):
    if files:
        download_list = set()
        print(f"Listing files to download into path: {path}")
        for index, (file_name, file_url) in enumerate(files):
            # Get suffix from url
            file_name_in_url = urlparse(file_url).path
            suffix = Path(file_name_in_url).suffix
            # Append to filename
            file_name = f"{index} - {file_name}{suffix}"
            file_name = sanitize_string(file_name)
            full_path = Path(path) / file_name
            # Add to download list
            download_list.add((file_url, str(full_path)))
        print("Downloading files...")
        downloader = Downloader()
        run(downloader.download_list_of_files(download_list))


def download_video(title, path, video_url):
    if video_url:
        print(f"Downloading Video: {path}")
        file_path = path / (title + ".mp4")
        if not file_path.exists():  # Download only if it didnt previously
            tries = 3
            for attempt in range(tries):
                try:
                    Downloader.download_video_mp4(video_url, path, title)
                except Exception as e:
                    logger.warning(f"Download failed for video: {video_url}")
                    logger.warning(f"Error: {str(e)}")
                    if attempt < tries - 1:
                        continue
                break
        else:
            print("Video Already Exists, skipping...")


def save_screenshot_as_pdf(page_loader, path, title):
    page_loader.send_devtools(
        "Emulation.setEmulatedMedia", {"media": "screen"}
    )
    pdf_options = {
        "paperHeight": 92,
        "paperWidth": 8,
        "printBackground": True,
    }
    page_loader.save_as_pdf(str(path / title) + ".pdf", pdf_options)


def save_screenshot(page_loader, title, path):
    print(f"Saving screenshot: {path/title}.png")
    page_loader.save_screenshot(str(path / title))
    page_loader.save_screenshot_as_pdf(str(path / title))


def save_page_html(page_loader, title, path):
    print(f"Saving Html: {path/title}.html")
    page_loader.save_html(path / title)


def create_lesson_path(path):
    print(f"Creating Path: {path}")
    path.mkdir(parents=True, exist_ok=True)


def show_lesson_info(title, path, files, video, assessment):
    print(
        f"title: {title}\npath: {path}\nvideo: {video}\nassessment: {assessment}\n"
    )
    if files:
        for file_name, file_link in files:
            print(f"files: {file_name} - {file_link[:30]}...")
