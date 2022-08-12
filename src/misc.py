import logging
import pickle
import sys
from collections import deque
from pathlib import Path


def file_path(filename):
    """File path relative to executable"""
    return str(Path(__file__).parent / filename)


def save_queue(queue: deque, queue_file: str = "queue.pkl"):
    with open(file_path(queue_file), "wb") as queue_file:
        pickle.dump(queue, queue_file)


def load_queue(queue_file: str = "queue.pkl") -> deque:
    with open(file_path(queue_file), "rb") as queue_file:
        queue = pickle.load(queue_file)
        return queue


def save_visited_links(visited_links: set, visited_links_file: str):
    with open(file_path(visited_links_file), "wb") as visited_links_file:
        pickle.dump(visited_links, visited_links_file)


def load_visited_links(visited_links_file: str) -> set:
    with open(file_path(visited_links_file), "rb") as visited_links_file:
        visited = pickle.load(visited_links_file)
        return visited


def sanitize_string(string):
    return (
        string.replace("#", "")
        .replace("|", "-")
        .replace("  ", " ")
        .replace("	", "")
        .replace("'", "")
        .replace('"', "")
    )


def set_logging_handlers(output_filename):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(output_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    return logger
