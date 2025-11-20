"""Simple Jira integration service template.

This file contains a minimal wrapper that other services can call to create
or update Jira issues from action items extracted from meetings.

Expected environment variables:
- JIRA_BASE_URL
- JIRA_API_TOKEN
- JIRA_USER_EMAIL
- JIRA_DEFAULT_PROJECT_KEY

Implement authentication and request handling per your Jira setup (Cloud/Server).
"""
import os
import requests

class JiraService:
    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.user_email = os.getenv("JIRA_USER_EMAIL")
        self.project_key = os.getenv("JIRA_DEFAULT_PROJECT_KEY")

    def _auth(self):
        return (self.user_email, self.api_token)

    def create_issue(self, title: str, description: str, issue_type: str = "Task") -> dict:
        """Create a Jira issue and return the API response as dict."""
        url = f"{self.base_url}/rest/api/2/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": title,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }
        resp = requests.post(url, json=payload, auth=self._auth())
        resp.raise_for_status()
        return resp.json()

    def add_comment(self, issue_key: str, comment: str) -> dict:
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}/comment"
        resp = requests.post(url, json={"body": comment}, auth=self._auth())
        resp.raise_for_status()
        return resp.json()
