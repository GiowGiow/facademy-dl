import asyncio
import json
from asyncio import Semaphore, gather, wait_for

import aiofile
import m3u8_To_MP4
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import InvalidURL

from misc import set_logging_handlers

MAX_TASKS = 5
MAX_TIME = 60

logger = set_logging_handlers("logs.log")


def get_cookie_string(json_obj: list):
    cookie_string = []
    for elem in json_obj:
        cookie_string.append(f"{elem['name']}={elem['value']}; ")
    return "".join(cookie_string)


class Downloader:
    cookie_string = None
    user_agent = None

    def __init__(
        self, cookie_file="cookies.json", user_agent_file="user_agent.txt"
    ):
        if not Downloader.cookie_string:
            j = json.loads(open(cookie_file, "r").read())
            Downloader.cookie_string = get_cookie_string(j)
        if not Downloader.user_agent:
            Downloader.user_agent = open(user_agent_file, "r").read()

    @classmethod
    async def download_list_of_files(file_list):
        tasks = []
        sem = Semaphore(MAX_TASKS)

        headers = {
            "cookie": Downloader.cookie_string,
            "user-agent": Downloader.user_agent,
        }

        async with ClientSession(headers=headers) as sess:
            for file_url, file_path in file_list:
                tasks.append(
                    # Wait max 60 seconds for each download
                    wait_for(
                        Downloader.download_one(
                            file_url, sess, sem, file_path
                        ),
                        timeout=MAX_TIME,
                    )
                )

            return await gather(*tasks)

    @classmethod
    async def download_one(url, session, semaphore, file_path):
        tries = 3
        for attempt in range(tries):
            try:
                # Try to make an async request to page
                async with semaphore:
                    async with session.get(url) as resp:
                        # The response was not what we expected
                        if not resp.ok:
                            logger.warning(
                                f"URL: {url}\nFILE:{file_path}\nInvalid status code: {resp.status}"
                            )
                            # Try again if possible
                            if attempt < tries - 1:
                                continue
                        # If response was successful
                        else:
                            # Try to download the file in chunks
                            try:
                                async with aiofile.async_open(
                                    file_path, "wb+"
                                ) as afp:
                                    async for chunk in resp.content.iter_chunked(
                                        1024 * 512
                                    ):  # 500 KB
                                        await afp.write(chunk)
                            # If there was an error downloading the file
                            except asyncio.TimeoutError:
                                logger.warning(
                                    f"A timeout ocurred while downloading '{file_path}' from {url}"
                                )
                                # Try again if possible
                                if attempt < tries - 1:
                                    continue
                            except Exception as e:
                                logger.warning(
                                    f"Failed to download file: {file_path}\n{e}"
                                )
                                if attempt < tries - 1:
                                    continue
                            break
            # The request failed
            except InvalidURL:
                logger.warning(f"Invalid URL: {url}\n FILE:{file_path}")
                # No point in trying, the URL is invalid
                break
            except Exception as e:
                logger.warning(f"Failed to download file: {file_path}\n{e}")
                if attempt < tries - 1:
                    continue
            break

    @staticmethod
    def download_video_mp4(video_url, mp4_file_dir, mp4_file_name):
        m3u8_To_MP4.async_download(
            video_url,
            mp4_file_dir=mp4_file_dir,
            mp4_file_name=mp4_file_name,
            max_retry_times=30,
            num_concurrent=100,
        )
