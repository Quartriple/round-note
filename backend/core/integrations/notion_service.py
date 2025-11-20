"""Notion integration service template.

This file contains a minimal wrapper to create pages or append content to Notion
workspaces using Notion API. Configure the integration token and default database
or parent page id via environment variables:

- NOTION_API_TOKEN
- NOTION_PARENT_PAGE_ID

See Notion API docs for details: https://developers.notion.com/
"""
import os
import requests

class NotionService:
    def __init__(self):
        self.api_token = os.getenv("NOTION_API_TOKEN")
        self.parent_page = os.getenv("NOTION_PARENT_PAGE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def create_page(self, title: str, content_blocks: list) -> dict:
        """Create a Notion page under configured parent page.

        `content_blocks` should be a list of Notion block dicts.
        """
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"page_id": self.parent_page},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": content_blocks
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def append_blocks(self, block_id: str, blocks: list) -> dict:
        url = f"{self.base_url}/blocks/{block_id}/children"
        resp = requests.patch(url, json={"children": blocks}, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
