import os
import logging

from notion_client import Client

from .ninegag import NineGagBot
from .notion import Notion

os.environ['PATH'] += r":/Users/maxence/Projects/9gag-notion-scraper"

START_STREAM = os.environ['START_STREAM']

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE = os.environ["NOTION_DATABASE"]

logger = logging.getLogger('app')


def main():
    notion = Notion(Client(auth=NOTION_TOKEN), NOTION_DATABASE)
    with NineGagBot() as bot:
        bot.landing_page()

        stream = int(START_STREAM)
        elements = None

        while True:

            # Waiting until next stream is detected or the spinner ends
            while True:
                elements = bot.get_elements_from_stream(stream)

                if elements:
                    for element in elements:
                        notion.add_gag(
                            element.name,
                            element.id,
                            element.url,
                            element.post_section,
                            element.cover_photo
                        )
                    elements = None
                    bot.scroll_to_spinner(sleep=1)
                    stream += 1

                if not bot.is_loader_spinning():
                    logger.info('Reached the bottom')
                    return

                # bot.scroll(sleep=0.1)


if __name__ == '__main__':
    main()
