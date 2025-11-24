"""Jira integration service for Round Note.

This service provides comprehensive Jira integration including:
- Project listing
- Issue creation and updates
- Priority and field mapping
- Multi-project support

Environment variables (fallback):
- JIRA_BASE_URL
- JIRA_API_TOKEN
- JIRA_USER_EMAIL
- JIRA_DEFAULT_PROJECT_KEY
"""
import os
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class JiraService:
    """Jira API integration service with flexible configuration."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: Optional[str] = None
    ):
        """
        Initialize Jira service with optional parameters.
        Falls back to environment variables if not provided.
        
        Args:
            base_url: Jira instance URL (e.g., https://yourcompany.atlassian.net)
            email: User email for authentication
            api_token: Jira API token
            project_key: Default project key (e.g., "PROJ")
        """
        self.base_url = base_url or os.getenv("JIRA_BASE_URL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        self.user_email = email or os.getenv("JIRA_USER_EMAIL")
        self.project_key = project_key or os.getenv("JIRA_DEFAULT_PROJECT_KEY")
        
        if not all([self.base_url, self.api_token, self.user_email]):
            raise ValueError("Jira credentials not configured. Provide base_url, email, and api_token.")

    def _auth(self) -> tuple:
        """Return authentication tuple for requests."""
        return (self.user_email, self.api_token)
    
    def _map_priority(self, rn_priority: Optional[str]) -> str:
        """
        Map Round Note priority to Jira priority.
        
        Args:
            rn_priority: Round Note priority (LOW/MEDIUM/HIGH)
            
        Returns:
            Jira priority name (Low/Medium/High)
        """
        priority_map = {
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High"
        }
        return priority_map.get(rn_priority, "Medium")
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Retrieve all projects accessible to the user.
        Supports both Company-managed and Team-managed projects.
        
        Returns:
            List of project dictionaries with keys: key, name, id
            Example: [{"key": "PROJ", "name": "My Project", "id": "10000"}]
        """
        # Try API v3 with search parameter to get all project types
        url = f"{self.base_url}/rest/api/3/project/search"
        resp = requests.get(url, auth=self._auth(), params={"expand": "description,lead"})
        
        print(f"[DEBUG] API v3 project/search status: {resp.status_code}")
        print(f"[DEBUG] API v3 response: {resp.text[:500]}")
        
        # Fallback to v2 if v3 fails
        if resp.status_code != 200:
            url = f"{self.base_url}/rest/api/2/project"
            resp = requests.get(url, auth=self._auth())
            print(f"[DEBUG] API v2 project status: {resp.status_code}")
            print(f"[DEBUG] API v2 response: {resp.text[:500]}")
        
        resp.raise_for_status()
        
        # Handle both response formats
        data = resp.json()
        print(f"[DEBUG] Parsed data type: {type(data)}")
        print(f"[DEBUG] Data keys: {data.keys() if isinstance(data, dict) else 'list'}")
        
        if isinstance(data, dict) and "values" in data:
            # v3 search response format
            projects = data["values"]
            print(f"[DEBUG] Found {len(projects)} projects in 'values'")
        else:
            # v2 response format (direct list)
            projects = data
            print(f"[DEBUG] Found {len(projects)} projects in list")
        
        return [
            {
                "key": p.get("key"),
                "name": p.get("name"),
                "id": p.get("id")
            }
            for p in projects
        ]
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Retrieve a Jira issue by key.
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            
        Returns:
            Issue data dictionary
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        resp = requests.get(url, auth=self._auth())
        resp.raise_for_status()
        return resp.json()

    def create_issue(
        self,
        title: str,
        description: str,
        project_key: Optional[str] = None,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        due_date: Optional[datetime] = None,
        assignee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Jira issue with full field mapping.
        
        Args:
            title: Issue summary/title
            description: Issue description
            project_key: Target project key (uses default if not provided)
            issue_type: Jira issue type (Task, Bug, Story, etc.)
            priority: Round Note priority (LOW/MEDIUM/HIGH)
            due_date: Due date as datetime object
            assignee_id: Jira account_id of assignee (optional)
            
        Returns:
            API response with issue key, id, and self link
        """
        project = project_key or self.project_key
        if not project:
            raise ValueError("No project key provided and no default configured")
        
        url = f"{self.base_url}/rest/api/2/issue"
        
        # Build fields
        fields = {
            "project": {"key": project},
            "summary": title,
            "description": description or "",
            "issuetype": {"name": issue_type}
        }
        
        # Add priority if provided
        if priority:
            jira_priority = self._map_priority(priority)
            fields["priority"] = {"name": jira_priority}
        
        # Add due date if provided
        if due_date:
            # Jira expects YYYY-MM-DD format
            fields["duedate"] = due_date.strftime("%Y-%m-%d")
        
        # Add assignee if provided (accountId)
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        
        payload = {"fields": fields}
        
        resp = requests.post(url, json=payload, auth=self._auth())
        resp.raise_for_status()
        return resp.json()
    
    def update_issue(
        self,
        issue_key: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing Jira issue.
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            title: New summary/title
            description: New description
            priority: New priority (LOW/MEDIUM/HIGH)
            due_date: New due date
            status: New status (requires transition, not implemented yet)
            assignee_id: Jira account_id of assignee (optional)
            
        Returns:
            API response (typically empty for successful updates)
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        
        # Build update fields
        fields = {}
        
        if title:
            fields["summary"] = title
        
        if description is not None:  # Allow empty string
            fields["description"] = description
        
        if priority:
            jira_priority = self._map_priority(priority)
            fields["priority"] = {"name": jira_priority}
        
        if due_date:
            fields["duedate"] = due_date.strftime("%Y-%m-%d")
        
        # Add assignee if provided (accountId)
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        
        if not fields:
            return {"message": "No fields to update"}
        
        payload = {"fields": fields}
        
        resp = requests.put(url, json=payload, auth=self._auth())
        resp.raise_for_status()
        
        # PUT returns 204 No Content on success
        return {"message": "Issue updated successfully", "issue_key": issue_key}

    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key: Jira issue key
            comment: Comment text
            
        Returns:
            Comment data
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}/comment"
        resp = requests.post(url, json={"body": comment}, auth=self._auth())
        resp.raise_for_status()
        return resp.json()
    
    def get_project_assignable_users(self, project_key: str) -> List[Dict[str, Any]]:
        """
        Get list of users who can be assigned issues in a project.
        
        Args:
            project_key: Jira project key
            
        Returns:
            List of user dictionaries with accountId, displayName, emailAddress
        """
        url = f"{self.base_url}/rest/api/3/user/assignable/search"
        params = {"project": project_key}
        resp = requests.get(url, auth=self._auth(), params=params)
        resp.raise_for_status()
        
        users = resp.json()
        return [
            {
                "account_id": u.get("accountId"),
                "display_name": u.get("displayName"),
                "email": u.get("emailAddress"),
                "avatar_url": u.get("avatarUrls", {}).get("48x48")
            }
            for u in users
        ]
    
    def get_project_priorities(self, project_key: str) -> List[Dict[str, Any]]:
        """
        Get list of available priorities for a project.
        
        Args:
            project_key: Jira project key
            
        Returns:
            List of priority dictionaries with id, name, iconUrl
        """
        # Get priorities from project metadata
        url = f"{self.base_url}/rest/api/3/priority"
        resp = requests.get(url, auth=self._auth())
        resp.raise_for_status()
        
        priorities = resp.json()
        return [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "icon_url": p.get("iconUrl"),
                "description": p.get("description", "")
            }
            for p in priorities
        ]
