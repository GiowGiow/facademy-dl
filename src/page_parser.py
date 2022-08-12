import json
from collections import OrderedDict
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class PageParser:
    BASE_URL = "https://cursos.fluencyacademy.io/"

    def __init__(self, fa_html):
        if not fa_html:
            return None
        self.soup = BeautifulSoup(fa_html, "html.parser")

    def find_video(self) -> str:
        video_link = self.soup.find("script", {"class": "w-json-ld"})
        if not video_link:
            return None
        video_link = json.loads(video_link.text)["contentUrl"]
        if not video_link:
            return None
        return video_link

    def find_post_downloads(self):
        post_downloads = self.soup.find("div", {"class": "download_cont"})
        if not post_downloads:
            return None

        files = []
        for link in post_downloads.find_all("a"):
            if not link.has_attr("href"):
                continue

            url = link["href"]
            name = link.find("span").text
            files.append((name, url))
        return files

    def get_lesson_path(self):
        course_path_div = self.soup.find("div", {"class": "breadcrumbs"}).text
        course_path = "/".join([s.strip() for s in course_path_div.split("/")])
        return course_path

    def get_lesson_title(self):
        return (
            self.soup.find("div", {"class": "breadcrumbs"})
            .text.split("/")[-1]
            .strip()
        )

    def find_section_lessons(self):
        lessons_div = self.soup.find("div", {"class": "category-listing"})
        section_title = lessons_div.find("h3", {"class": "title"}).text
        lesson_links = lessons_div.find_all("a")
        lesson_links = [
            urljoin(self.BASE_URL, link["href"]) for link in lesson_links
        ]
        return section_title, lesson_links

    def get_modules(self):
        modules_dict = OrderedDict()
        modules = self.soup.find_all("li", {"class": "cat_menu"})
        for module in modules:
            # Find module name
            module_name = module.find("a").text
            if not module_name:
                continue
            module_name = module_name.strip()  # name of the main module

            # Find module link
            module_link = None
            if module.find("a").has_attr("href"):
                module_link = module.find("a")["href"]

            modules_dict[module_name] = OrderedDict()
            if module_link:
                modules_dict[module_name]["link"] = urljoin(
                    self.BASE_URL, module_link
                )

            # Get list of submodules
            submodules = module.find_all("li", {"class": "cat_list"})
            if not submodules:
                continue

            # Parse list of submodules
            modules_dict[module_name]["submodules"] = OrderedDict()
            for submodule in submodules:
                submodule_link = submodule.find("a")["href"]
                submodule_name = submodule.find("p").text
                if (not submodule_link) or (not submodule_name):
                    continue
                modules_dict[module_name]["submodules"][submodule_name] = {}
                modules_dict[module_name]["submodules"][submodule_name][
                    "link"
                ] = urljoin(self.BASE_URL, submodule_link)

        return modules_dict

    def find_assessment(self) -> str | None:
        assessment_html = self.soup.find(
            "div", {"class": "assessment-wrapper"}
        )
        if not assessment_html:
            return None

        assessment_html = self.soup.find(
            "div", {"class": "assessment-wrapper"}
        )
        assessment_iframe = assessment_html.find("iframe")
        if assessment_iframe.has_attr("src"):
            assess_url = assessment_iframe["src"]
            assess_url = assess_url.split("?")[0]
            return urljoin(self.BASE_URL, assess_url)

        return None
