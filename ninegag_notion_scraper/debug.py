from notion_client import Client as NotionClient


from .args import Arguments
from .env import Environments


def main(args: Arguments, envs: Environments):
    from .infra.repo.meme_notion.get_memes import NotionGetMemes

    notion = NotionGetMemes(NotionClient(
        auth=envs.NOTION_TOKEN), envs.NOTION_DATABASE)

    memes = notion.get_memes(filter=None)

    for meme in memes:
        print(meme)
