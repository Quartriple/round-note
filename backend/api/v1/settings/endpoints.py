"""Settings management endpoints for integrations."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import ulid
import json
import requests

from backend.dependencies import get_db, get_current_user
from backend import models
from backend.core.auth.encryption import encrypt_data, decrypt_data
from backend.core.integrations import JiraService


router = APIRouter(prefix="/settings", tags=["Settings"])


# ==================== Pydantic Schemas ====================

class JiraSettingsIn(BaseModel):
    """Jira settings input schema."""
    base_url: str
    email: str
    api_token: str
    default_project_key: Optional[str] = None


class JiraSettingsOut(BaseModel):
    """Jira settings output schema (without sensitive data)."""
    base_url: str
    email: str
    default_project_key: Optional[str] = None
    is_active: bool
    created_dt: str
    updated_dt: Optional[str] = None


# ==================== Endpoints ====================

@router.post("/jira", status_code=status.HTTP_201_CREATED)
async def save_jira_settings(
    settings: JiraSettingsIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Save or update Jira integration settings for a user.
    
    Encrypts sensitive data (API token) before storing in database.
    """
    user_id = current_user.USER_ID
    try:
        # Test Jira connection before saving
        jira = JiraService(
            base_url=settings.base_url,
            email=settings.email,
            api_token=settings.api_token,
            project_key=settings.default_project_key
        )
        
        # Validate connection by fetching projects
        try:
            projects = jira.get_projects()
            projects_count = len(projects) if projects else 0
            
            # 프로젝트가 없어도 연결 성공이면 허용 (경고만 출력)
            if projects_count == 0:
                print("[WARNING] No projects found, but connection succeeded. User may have limited permissions.")
        except requests.exceptions.HTTPError as e:
            # HTTP 에러는 연결 실패로 간주
            error_detail = f"Jira API error {e.response.status_code}"
            try:
                error_json = e.response.json()
                if "errorMessages" in error_json:
                    error_detail += f": {', '.join(error_json['errorMessages'])}"
                elif "message" in error_json:
                    error_detail += f": {error_json['message']}"
            except:
                error_detail += f": {e.response.text[:200]}"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Jira: {str(e)}"
            )
        
        # Encrypt sensitive data
        encrypted_config = {
            "base_url": settings.base_url,
            "email": settings.email,
            "api_token": encrypt_data(settings.api_token),  # Encrypt API token
            "default_project_key": settings.default_project_key
        }
        
        # Check if settings already exist
        existing = db.query(models.UserIntegrationSetting).filter(
            models.UserIntegrationSetting.USER_ID == user_id,
            models.UserIntegrationSetting.PLATFORM == "jira"
        ).first()
        
        if existing:
            # Update existing settings
            existing.CONFIG = encrypted_config
            existing.IS_ACTIVE = 'Y'
            db.commit()
            db.refresh(existing)
            
            return {
                "message": "Jira settings updated successfully",
                "projects_found": projects_count
            }
        else:
            # Create new settings
            new_setting = models.UserIntegrationSetting(
                INTEGRATION_ID=str(ulid.new()),
                USER_ID=user_id,
                PLATFORM="jira",
                CONFIG=encrypted_config,
                IS_ACTIVE='Y'
            )
            db.add(new_setting)
            db.commit()
            db.refresh(new_setting)
            
            return {
                "message": "Jira settings saved successfully",
                "projects_found": projects_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save Jira settings: {str(e)}"
        )


@router.get("/jira", response_model=JiraSettingsOut)
async def get_jira_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve Jira settings for a user (without API token).
    """
    user_id = current_user.USER_ID
    setting = db.query(models.UserIntegrationSetting).filter(
        models.UserIntegrationSetting.USER_ID == user_id,
        models.UserIntegrationSetting.PLATFORM == "jira"
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jira settings not found. Please configure Jira integration first."
        )
    
    config = setting.CONFIG
    
    return JiraSettingsOut(
        base_url=config.get("base_url", ""),
        email=config.get("email", ""),
        default_project_key=config.get("default_project_key"),
        is_active=setting.IS_ACTIVE == 'Y',
        created_dt=setting.CREATED_DT.isoformat() if setting.CREATED_DT else "",
        updated_dt=setting.UPDATED_DT.isoformat() if setting.UPDATED_DT else None
    )


@router.delete("/jira", status_code=status.HTTP_200_OK)
async def delete_jira_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete Jira integration settings for a user.
    """
    user_id = current_user.USER_ID
    setting = db.query(models.UserIntegrationSetting).filter(
        models.UserIntegrationSetting.USER_ID == user_id,
        models.UserIntegrationSetting.PLATFORM == "jira"
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jira settings not found"
        )
    
    db.delete(setting)
    db.commit()
    
    return {"message": "Jira settings deleted successfully"}


@router.get("/jira/projects")
async def get_jira_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get list of Jira projects accessible to the user.
    """
    user_id = current_user.USER_ID
    # Retrieve user's Jira settings
    setting = db.query(models.UserIntegrationSetting).filter(
        models.UserIntegrationSetting.USER_ID == user_id,
        models.UserIntegrationSetting.PLATFORM == "jira"
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jira not configured. Please set up Jira integration in settings."
        )
    
    try:
        config = setting.CONFIG
        
        # Decrypt API token
        decrypted_token = decrypt_data(config["api_token"])
        
        # Initialize Jira service
        jira = JiraService(
            base_url=config["base_url"],
            email=config["email"],
            api_token=decrypted_token,
            project_key=config.get("default_project_key")
        )
        
        # Fetch projects
        projects = jira.get_projects()
        
        return {
            "projects": projects,
            "default_project_key": config.get("default_project_key")
        }
        
    except requests.exceptions.RequestException as e:
        # Network/HTTP errors from Jira API
        error_detail = f"Jira API request failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_detail += f" (Status: {e.response.status_code})"
            try:
                error_json = e.response.json()
                if "errorMessages" in error_json:
                    error_detail += f" - {', '.join(error_json['errorMessages'])}"
            except:
                pass
        print(f"[ERROR] {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )
    except Exception as e:
        # Other errors (decryption, parsing, etc.)
        error_detail = f"Failed to fetch Jira projects: {type(e).__name__}: {str(e)}"
        print(f"[ERROR] {error_detail}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Jira projects: {str(e)}"
        )


@router.get("/jira/projects/{project_key}/users")
async def get_jira_project_users(
    project_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get assignable users for a Jira project.
    """
    user_id = current_user.USER_ID
    
    # Retrieve user's Jira settings
    setting = db.query(models.UserIntegrationSetting).filter(
        models.UserIntegrationSetting.USER_ID == user_id,
        models.UserIntegrationSetting.PLATFORM == "jira"
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jira not configured"
        )
    
    try:
        config = setting.CONFIG
        decrypted_token = decrypt_data(config["api_token"])
        
        jira = JiraService(
            base_url=config["base_url"],
            email=config["email"],
            api_token=decrypted_token,
            project_key=project_key
        )
        
        users = jira.get_project_assignable_users(project_key)
        
        return {"users": users}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Jira users: {str(e)}"
        )


@router.get("/jira/projects/{project_key}/priorities")
async def get_jira_project_priorities(
    project_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get available priorities for a Jira project.
    """
    user_id = current_user.USER_ID
    
    # Retrieve user's Jira settings
    setting = db.query(models.UserIntegrationSetting).filter(
        models.UserIntegrationSetting.USER_ID == user_id,
        models.UserIntegrationSetting.PLATFORM == "jira"
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jira not configured"
        )
    
    try:
        config = setting.CONFIG
        decrypted_token = decrypt_data(config["api_token"])
        
        jira = JiraService(
            base_url=config["base_url"],
            email=config["email"],
            api_token=decrypted_token,
            project_key=project_key
        )
        
        priorities = jira.get_project_priorities(project_key)
        
        return {"priorities": priorities}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Jira priorities: {str(e)}"
        )
