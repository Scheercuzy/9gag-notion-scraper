"""The main function"""

import logging
from typing import Callable
from notion_client import Client as NotionClient
from selenium.webdriver.remote.webdriver import WebDriver

from ninegag_notion_scraper.app.use_cases.meme import GetMeme, GetMemes, \
    SaveMeme
from ninegag_notion_scraper.infrastructure.meme_ninegag_scraper.page_single \
    import Meme404, NineGagSinglePageScraperRepo
from ninegag_notion_scraper.infrastructure.meme_notion.get_memes \
    import NotionGetMemes

# Setup tools
from .env import Environments, get_envs
from .cli import Arguments, get_args
from .webdriver import get_webdriver

from .app.entities.meme import Meme
from .app.use_cases.cookies import CookiesUseCase
from .infrastructure.cookie_filestorage \
    import FileCookiesRepo
from .infrastructure.meme_ninegag_scraper import NineGagStreamScraperRepo
from .infrastructure.meme_notion import NotionSaveMeme
from .infrastructure.meme_filestorage import FileStorageRepo

logger = logging.getLogger('app')


def main(args: Arguments, envs: Environments,
         get_webdriver: Callable[[], WebDriver]) -> None:
    """The entry point to the application"""

    webdriver = get_webdriver()

    cookie_usecase = CookiesUseCase(FileCookiesRepo())

    if args.save_notion_meme_locally:
        notion = NotionGetMemes(NotionClient(
            auth=envs.NOTION_TOKEN), envs.NOTION_DATABASE)
        file_storage = FileStorageRepo(
            covers_path=envs.COVERS_PATH,
            memes_path=envs.MEMES_PATH,
            _selenium_cookies_func=cookie_usecase.get_cookies
        )
        ninegag = NineGagSinglePageScraperRepo(
            envs.NINEGAG_USERNAME,
            envs.NINEGAG_PASSWORD,
            webdriver,
            cookie_usecase
        )
        with ninegag:
            memes_from_notion_to_save_locally(
                notion=GetMemes(notion),
                file_storage=SaveMeme(file_storage),
                ninegag=GetMeme(ninegag),
                args=args
            )
        return

    ninegag_scraper_repo = NineGagStreamScraperRepo(
        envs.NINEGAG_URL,
        envs.NINEGAG_USERNAME,
        envs.NINEGAG_PASSWORD,
        webdriver,
        cookie_usecase
    )

    notion_storage_repo = NotionSaveMeme(NotionClient(
        auth=envs.NOTION_TOKEN), envs.NOTION_DATABASE
    )

    filestorage_repo = FileStorageRepo(
        covers_path=envs.COVERS_PATH,
        memes_path=envs.MEMES_PATH,
        _selenium_cookies_func=cookie_usecase.get_cookies
    )

    with ninegag_scraper_repo:

        memes_from_9gag_to_notion_with_local_save(
            ninegag=GetMemes(ninegag_scraper_repo),
            notion=SaveMeme(notion_storage_repo),
            file_storage=SaveMeme(filestorage_repo),
            args=args
        )


class StopLoopException(Exception):
    pass


def memes_from_9gag_to_notion_with_local_save(
        ninegag: GetMemes,
        notion: SaveMeme,
        file_storage: SaveMeme,
        args: Arguments) -> None:

    for memes in ninegag.get_memes():
        try:
            for meme in memes:
                evaluate_storage(args, meme, file_storage)
                evaluate_storage(args, meme, notion)

        except StopLoopException:
            logger.debug("Loop stopped by evaluate_storage")


def evaluate_storage(args: Arguments,
                     meme: Meme,
                     storage: SaveMeme):

    exists = storage.meme_exists(meme)

    if args.skip_existing and exists:
        logger.info(f"Meme ID {meme.item_id} was skipped "
                    f"in '{storage.__class__.__name__}' because it "
                    "already exists")
        return

    if args.stop_existing and exists:
        raise StopLoopException  # stop the outer loop

    storage.save_meme(meme)


def memes_from_notion_to_save_locally(
        notion: GetMemes,
        file_storage: SaveMeme,
        ninegag: GetMeme,
        args: Arguments
):
    for memes in notion.get_memes():
        try:
            for meme in memes:
                if not file_storage.meme_exists(meme):
                    logger.info(f"Meme {meme.item_id} doesn't exists locally")

                    try:
                        loaded_meme = ninegag.get_meme_from_url(
                            meme.post_web_url)
                    except Meme404:
                        logger.info(
                            f"skipping Meme ID {meme.item_id} because it "
                            "doesn't exist anymore")
                        continue

                    evaluate_storage(args, loaded_meme, file_storage)
                else:
                    logger.info(f"Meme {meme.item_id} already exists")
        except StopLoopException:
            logger.debug("Loop stopped by evaluate_storage")


if __name__ == '__main__':
    args = get_args()
    envs = get_envs()

    if args.debug:
        from .debug import main as debug
        debug(args, envs)
        quit()

    main(args=args, envs=envs, get_webdriver=get_webdriver)
