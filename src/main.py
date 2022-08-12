import sys

from clean_page import clean_pages
from crawler import crawl, get_queue
from make_page_local import download_assets_and_edit_htmls
from page_loader import PageLoader
from page_parser import PageParser

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 main.py project_folder")
    project_folder = sys.argv[1]
    page_loader = PageLoader()
    bem_vindo_page = ""
    print(f"Loading first page: {bem_vindo_page}")
    page_html = page_loader.load_page(bem_vindo_page)
    if not page_html:
        print("Failed to load page...")
        sys.exit(1)

    print("Parsing first page...")
    parser = PageParser(page_html)

    # This are the webpages that have the same structure
    # and that we want to crawl
    modules_to_crawl = [
        "Bem-Vindo",
        "Bem-vindo",
        "Welcome",
        "Benvenuti",
        "¡Bienvenido!",
        "Bienvenue",
        "Minicurso",
        "Wave 01",
        "Wave 02",
        "Onda 1",
        "Onda 2",
        "Onda 01",
        "Onda 02",
        "Morceau 01",
        "Morceau 02",
        "파도 2",
        "Extra",
        "Extras",  # If they have any
    ]

    queue, visited_links = get_queue(parser, modules_to_crawl)
    page_loader.driver.close()
    page_loader.driver.quit()
    while True:
        try:
            crawl(queue, visited_links)
            break
        except Exception as e:
            print(f"Error while crawling, trying again... {e}")
            pass
    download_assets_and_edit_htmls(project_folder)
    clean_pages(project_folder)
