from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, cast
import os
import glob
from pathlib import Path
from datetime import datetime

from src.api.database.connection import get_auth_db, get_fim_db
from src.api.utils.jwt_utils import verify_token
from src.api.models.user_model import User
from src.api.models.fim_models import Directory, FileMetadata
from src.FIM.FIM import monitor_changes
from src.utils.backup import Backup

# Import schemas
from src.api.schemas.fim_schema import (
    FIMStartRequest, 
    FIMStopRequest, 
    FIMAddPathRequest,
    FIMRestoreRequest,
    FIMStatusResponse,
    FIMChangesResponse,
    FIMLogsResponse
)

router = APIRouter(prefix="/api/fim", tags=["File Integrity Monitoring"])

fim_monitor = monitor_changes()

# Helper function to verify admin access
def verify_admin_access(token_data: dict = Depends(verify_token), db: Session = Depends(get_auth_db)) -> User:
    """Verify that the current user is an admin"""
    admin = db.query(User).filter(User.email == token_data["sub"]).first()
    if not admin or not getattr(admin, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin

@router.post("/start", summary="Start monitoring directories")
def start_fim_monitoring(
    request: FIMStartRequest,
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(verify_admin_access),
    auth_db: Session = Depends(get_auth_db),
    fim_db: Session = Depends(get_fim_db)
):
    """
    Start monitoring specified directories for file integrity changes.
    """
    try:
        # Verify directories exist
        for directory in request.directories:
            if not os.path.exists(directory):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Directory does not exist: {directory}"
                )

        for directory in request.directories:
            existing_dir = fim_db.query(Directory).filter(Directory.path == directory).first()
            if not existing_dir:
                new_dir = Directory(path=directory)
                fim_db.add(new_dir)
        
        fim_db.commit()

        background_tasks.add_task(
            fim_monitor.monitor_changes,
            admin_user.username,
            request.directories,
            request.excluded_files or []
        )

        return {
            "message": "FIM monitoring started successfully",
            "directories": request.directories,
            "excluded_files": request.excluded_files or []
        }

    except Exception as e:
        fim_db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/stop", summary="Stop monitoring directories")
def stop_fim_monitoring(
    request: FIMStopRequest,
    admin_user: User = Depends(verify_admin_access),
    auth_db: Session = Depends(get_auth_db)
):
    """
    Stop monitoring specified directories.
    """
    try:
        # Stop the observer if it's running
        if hasattr(fim_monitor, 'observer') and fim_monitor.observer.is_alive():
            fim_monitor.observer.stop()
            fim_monitor.observer.join()

        return {
            "message": "FIM monitoring stopped successfully",
            "stopped_directories": request.directories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/status", response_model=FIMStatusResponse, summary="Get monitoring status")
def get_fim_status(
    token_data: dict = Depends(verify_token),
    auth_db: Session = Depends(get_auth_db),
    fim_db: Session = Depends(get_fim_db)
):
    """
    Get current FIM monitoring status and watched directories.
    """
    try:
        is_monitoring = (
            hasattr(fim_monitor, 'observer') and 
            fim_monitor.observer.is_alive()
        )

        dir_records = fim_db.query(Directory).all()
        watched_directories = [str(d.path) for d in dir_records]

        return FIMStatusResponse(
            is_monitoring=is_monitoring,
            watched_directories=watched_directories,
            total_watched=len(watched_directories)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/changes", response_model=FIMChangesResponse, summary="Get detected changes")
def get_fim_changes(
    directory: Optional[str] = None,
    token_data: dict = Depends(verify_token),
    auth_db: Session = Depends(get_auth_db),
    fim_db: Session = Depends(get_fim_db)
):
    """
    Fetch latest detected file changes from FIM database.
    """
    try:
        query = fim_db.query(FileMetadata).filter(FileMetadata.status != 'current')
        
        if directory:
            dir_record = fim_db.query(Directory).filter(Directory.path == directory).first()
            if dir_record:
                query = query.filter(FileMetadata.directory_id == dir_record.id)
        
        changes_data = query.order_by(FileMetadata.detected_at.desc()).all()
        
        # Organize changes by type
        changes = {"added": {}, "modified": {}, "deleted": {}}
        
        for change in changes_data:
            dir_path = fim_db.query(Directory.path).filter(Directory.id == change.directory_id).scalar()
            full_path = change.item_path
            
            change_info = {
                "hash": change.hash,
                "last_modified": change.last_modified.strftime("%Y-%m-%d %H:%M:%S") if change.last_modified is not None else None,
                "type": change.item_type,
                "detected_at": change.detected_at.strftime("%Y-%m-%d %H:%M:%S") if change.detected_at is not None else None
            }
            
            if cast(str, change.status) == 'added':
                changes["added"][full_path] = change_info
            elif cast(str, change.status) == 'modified':
                changes["modified"][full_path] = change_info
            elif cast(str, change.status) == 'deleted':
                changes["deleted"][full_path] = change_info

        total_changes = len(changes_data)
        
        return FIMChangesResponse(
            added=changes["added"],
            modified=changes["modified"],
            deleted=changes["deleted"],
            total_changes=total_changes
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get changes: {str(e)}")

@router.get("/logs", response_model=List[FIMLogsResponse], summary="Retrieve FIM logs")
def get_fim_logs(
    directory: Optional[str] = None,
    token_data: dict = Depends(verify_token),
    auth_db: Session = Depends(get_auth_db)
):
    """
    Retrieve logs from FIM log files.
    """
    try:
        logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        logs = []

        if directory:
            # Get specific directory logs
            norm_dir = Path(directory).resolve().name
            log_file = logs_dir / f"FIM_{norm_dir}.log"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logs.append(FIMLogsResponse(
                        directory=directory,
                        log_file=str(log_file),
                        content=content
                    ))
            else:
                raise HTTPException(status_code=404, detail=f"No logs found for directory: {directory}")
        else:
            for log_path in logs_dir.glob("FIM_*.log"):
                directory_name = log_path.stem.replace("FIM_", "")
                
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logs.append(FIMLogsResponse(
                        directory=directory_name,
                        log_file=str(log_path),
                        content=content
                    ))

        if not logs:
            raise HTTPException(status_code=404, detail="No FIM logs found")

        return logs

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

@router.post("/restore", summary="Restore files from backup")
def restore_files(
    request: FIMRestoreRequest,
    admin_user: User = Depends(verify_admin_access),
    auth_db: Session = Depends(get_auth_db)
):
    """
    Restore files or directories from backup.
    """
    try:
        backup_instance = Backup()
        
        # Restore the specified path
        result = backup_instance.restore_backup(
            request.path_to_restore,
            admin_user.username  # ✅ Use admin_user
        )

        if result:
            return {
                "message": "Restore completed successfully",
                "restored_path": request.path_to_restore
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to restore: {request.path_to_restore}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.post("/add-path", summary="Add directory to monitor")
def add_monitoring_path(
    request: FIMAddPathRequest,
    admin_user: User = Depends(verify_admin_access),
    auth_db: Session = Depends(get_auth_db),
    fim_db: Session = Depends(get_fim_db)
):
    """
    Add a new directory to the monitoring list.
    """
    try:
        if not os.path.exists(request.directory):
            raise HTTPException(
                status_code=400, 
                detail=f"Directory does not exist: {request.directory}"
            )

        # Check if directory already exists in database
        existing_dir = fim_db.query(Directory).filter(Directory.path == request.directory).first()
        if existing_dir:
            raise HTTPException(
                status_code=400, 
                detail="Directory is already being monitored"
            )

        new_dir = Directory(path=request.directory)
        fim_db.add(new_dir)
        fim_db.commit()

        # Update in-memory directories if monitoring is active
        if hasattr(fim_monitor, 'current_directories'):
            if request.directory not in fim_monitor.current_directories:
                fim_monitor.current_directories.append(request.directory)

        return {
            "message": "Directory added to monitoring",
            "directory": request.directory,
            "total_monitored": len(fim_monitor.current_directories) if hasattr(fim_monitor, 'current_directories') else 1
        }

    except Exception as e:
        fim_db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to add directory: {str(e)}")

@router.post("/reset-baseline", summary="Reset baseline for directories")
def reset_baseline(
    request: FIMStartRequest,
    admin_user: User = Depends(verify_admin_access),
    auth_db: Session = Depends(get_auth_db)
):
    """
    Reset baseline for specified directories.
    """
    try:
        fim_monitor.reset_baseline(cast(str, admin_user.username), request.directories)

        return {
            "message": "Baseline reset successfully",
            "directories": request.directories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset baseline: {str(e)}")

@router.get("/baseline", summary="Get current baseline")
def get_baseline(
    directory: Optional[str] = None,
    token_data: dict = Depends(verify_token),
    auth_db: Session = Depends(get_auth_db),
    fim_db: Session = Depends(get_fim_db)
):
    """
    Get current baseline data for directories.
    """
    try:
        query = fim_db.query(FileMetadata).filter(FileMetadata.status == 'current')
        
        if directory:
            dir_record = fim_db.query(Directory).filter(Directory.path == directory).first()
            if dir_record:
                query = query.filter(FileMetadata.directory_id == dir_record.id)
            else:
                raise HTTPException(status_code=404, detail=f"Directory not found: {directory}")
        
        baseline_data = query.all()
        
        baseline = {}
        for item in baseline_data:
            dir_path = fim_db.query(Directory.path).filter(Directory.id == item.directory_id).scalar()
            if dir_path not in baseline:
                baseline[dir_path] = {}
            
            baseline[dir_path][item.item_path] = {
                "type": item.item_type,
                "hash": item.hash,
                "last_modified": item.last_modified.strftime("%Y-%m-%d %H:%M:%S") if item.last_modified is not None else None
            }

        return {
            "baseline": baseline,
            "total_items": len(baseline_data)
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to get baseline: {str(e)}")
