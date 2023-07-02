"""The main function"""

import os
import logging
from typing import List, Optional, Protocol
from notion_client import Client as NotionClient
from .ninegag import NineGagTools
from .storage.notion import NotionTools
from .storage.file_storage import FileStorage

os.environ['PATH'] += r":/Users/maxence/Projects/9gag-notion-scraper"

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE = os.environ["NOTION_DATABASE"]

NINEGAG_USERNAME = os.environ['USERNAME']
NINEGAG_PASSWORD = os.environ['PASSWORD']
NINEGAG_URL = os.environ['9GAG_URL']

logger = logging.getLogger('app')


class MemeData(Protocol):
    """Data required from a meme"""
    name: str
    id: str
    url: str
    post_section: list
    cover_photo: str


class MemeScrapperProtocol(Protocol):
    """Protocol for interaction needed on the meme site"""
    at_bottom_flag: bool

    def __init__(self, root_url: str, username: str,
                 password: str) -> None: ...

    def __enter__(self): ...

    def __exit__(self, exception_type, exception_value, traceback): ...

    def setup(self):
        """Setup everything needed as well as to go the root url"""

    def get_memes(self) -> List[MemeData]:
        """Get all memes from the current place on the page"""

    def next_page(self) -> Optional[int]:
        """Goes to the next set of memes"""


def main():
    """The entry point to the application"""
    memes_from_9gag_to_notion_with_local_save(
        NineGagTools(NINEGAG_URL, NINEGAG_USERNAME, NINEGAG_PASSWORD),
        NotionTools(NotionClient(auth=NOTION_TOKEN), NOTION_DATABASE),
        FileStorage("./dump")
    )


def memes_from_9gag_to_notion_with_local_save(
        ninegag: MemeScrapperProtocol,
        notion: NotionTools,
        storage: FileStorage) -> None:

    with ninegag:

        elements: List[MemeData]

        # Waiting until next stream is detected or the spinner ends
        while not ninegag.at_bottom_flag:
            elements = ninegag.get_memes()

            for element in elements:
                notion.add_gag(
                    name=element.name,
                    item_id=element.id,
                    url=element.url,
                    post_section=element.post_section,
                    cover_photo=element.cover_photo
                )
                # storage.save_cover_from_url(
                #     element.cover_photo,
                #     element.id
                # )
            ninegag.next_page()


if __name__ == '__main__':
    main()
