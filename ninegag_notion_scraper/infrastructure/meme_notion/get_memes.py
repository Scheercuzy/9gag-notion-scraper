import copy
from typing import Awaitable, List
from notion_client import Client
from ninegag_notion_scraper.app.entities.meme import Meme
from ninegag_notion_scraper.app.interfaces.repositories.meme \
    import GetMemesRepo
from ninegag_notion_scraper.infrastructure.meme_notion.base import NotionBase


from .converters import PageNameConverter, ItemIDConverter, PostURLConverter, \
    TagsConverter, CoverURLConverter


class NotionGetMemes(NotionBase, GetMemesRepo):
    def __init__(self, client: Client, database_id: str) -> None:
        NotionBase.__init__(self, client, database_id)
        self.at_end = False
        self._next_cursor = None
        self._current_cursor = None
        self._has_more = None
        self._next_count = 0

    def get_memes(self) -> List[Meme]:
        if self._current_cursor:
            query = self._client.databases.query(
                self._db_id,
                start_cursor=self._current_cursor
            )
        else:
            query = self._client.databases.query(self._db_id)

        assert not isinstance(query, Awaitable)
        pages: list = query.get('results')

        memes = []

        for page in pages:
            memes.append(Meme(
                title=PageNameConverter.decode(page),
                item_id=ItemIDConverter.decode(page),
                post_web_url=PostURLConverter.decode(page),
                tags=TagsConverter.decode(page),
                cover_photo_url=CoverURLConverter.decode(page),
                post_file_url=None
            ))

        self._next_cursor = query['next_cursor']
        self._has_more = query['has_more']

        return memes

    def next(self) -> int:
        if not self._has_more:
            self.at_end = True
            return self._next_count

        self._current_cursor = copy.deepcopy(self._next_cursor)
        self._next_count += 1
        return self._next_count

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass