import sys
from pathlib import Path

from bs4 import BeautifulSoup
from tqdm import tqdm


def sanitize_string(string):
    return (
        str(string)
        .replace("#", "")
        .replace("|", "-")
        .replace("  ", " ")
        .replace("	", "")
        .replace("'", "")
        .replace('"', "")
    )


def sanitize_folder_names(folder, apply=False):
    print("Sanitizing Folder Names")
    data_path = Path(folder)
    print("Getting all folders")
    subdirs = data_path.glob("*/*/*")
    for subdir in tqdm(subdirs):
        if not subdir.is_dir():
            continue
        if any(
            substring in str(subdir)
            for substring in ["/css", "/js", "/img", "/assessment"]
        ):
            continue
        path_as_str = str(subdir)
        new_name = sanitize_string(subdir.parent / str(subdir.name))
        if path_as_str == new_name:
            continue
        print(f"Old name: {path_as_str}")
        print(f"New name: {new_name}")
        if apply:
            subdir.rename(new_name)


def get_valid_files(files):
    """Files which are not assets"""
    filtered_files = []
    for file in tqdm(files):
        file = str(file)
        if not any(
            substring in file for substring in ["/css/", "/js/", "/img/"]
        ):
            filtered_files.append(file)
    return filtered_files


def sanitize_file_names(path, apply=False):
    print("Sanitizing file names")
    files_to_edit = []
    folder_path = Path(path)
    print("Getting all files")
    for ext in ["html", "css", "png", "mp3", "pdf", "zip", "mp4"]:
        files_to_edit.extend(folder_path.glob(f"**/*.{ext}"))

    for file in tqdm(files_to_edit):
        path_as_str = str(file)
        new_name = sanitize_string(file.name)
        new_name = str(file.parent / new_name)
        if new_name == path_as_str:
            continue
        print(f"Old name: {path_as_str}")
        print(f"New name: {new_name}")
        if apply:
            file.rename(new_name)


def remove_scripts_and_sanitize_mp4_inside_html(path):
    print("Changing video in html, removing scripts, removing broken images")
    files_to_edit = []
    folder_path = Path(path)

    print("Getting all htmls")
    for ext in ["html"]:
        files_to_edit.extend(folder_path.glob(f"**/*-giow.{ext}"))

    for file in tqdm(files_to_edit):
        with file.open("r") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            video = soup.find("source")
            # Sanitize video string
            if video:
                if video.has_attr("src"):
                    video["src"] = sanitize_string(video["src"])

        # Remove broken images
        imgs = soup.find_all("img", {"src": "img/img"})
        for img in imgs:
            img.decompose()

        # Remove scripts from pages that don't need them
        if "assessment" not in str(file):
            for script in soup("script"):
                script.decompose()

        with file.open("w") as f:
            f.write(str(soup))


def clean_pages(path):
    sanitize_folder_names(path, apply=True)
    sanitize_file_names(path, apply=True)
    remove_scripts_and_sanitize_mp4_inside_html(path)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        path = sys.argv[1]
        clean_pages(path)
