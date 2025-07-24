import os
import boto3
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from app.core.security import get_current_org
from app.core.config import get_settings
import tempfile
from io import BytesIO

router = APIRouter(prefix="/assets", tags=["Assets"])

settings = get_settings()

# Initialize Supabase Storage client (using boto3 for S3 compatibility)
def get_storage_client():
    return boto3.client(
        's3',
        endpoint_url=settings.SUPABASE_STORAGE_URL,
        region_name=settings.SUPABASE_STORAGE_REGION,
        aws_access_key_id=settings.SUPABASE_STORAGE_ACCESS_KEY_ID,
        aws_secret_access_key=settings.SUPABASE_STORAGE_SECRET_ACCESS_KEY
    )

def get_asset_key(org_id: str, asset_type: str) -> str:
    """Generate asset key for Supabase storage"""
    return f"{org_id}/assets/{asset_type}.png"

@router.get("/logo")
def get_logo(org_id: str = Depends(get_current_org)):
    try:
        s3_client = get_storage_client()
        asset_key = get_asset_key(org_id, "logo")
        
        # Try to get the object from Supabase storage
        response = s3_client.get_object(
            Bucket=settings.SUPABASE_STORAGE_BUCKET,
            Key=asset_key
        )
        
        # Return the file as a streaming response
        return StreamingResponse(
            response['Body'],
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=logo.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Logo not found")

@router.post("/logo")
def upload_logo(file: UploadFile = File(...), org_id: str = Depends(get_current_org)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        s3_client = get_storage_client()
        asset_key = get_asset_key(org_id, "logo")
        
        # Read file content
        file_content = file.file.read()
        
        # Upload to Supabase storage
        s3_client.put_object(
            Bucket=settings.SUPABASE_STORAGE_BUCKET,
            Key=asset_key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        return {"detail": "Logo uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload logo: {str(e)}")

@router.get("/signature")
def get_signature(org_id: str = Depends(get_current_org)):
    try:
        s3_client = get_storage_client()
        asset_key = get_asset_key(org_id, "signature")
        
        # Try to get the object from Supabase storage
        response = s3_client.get_object(
            Bucket=settings.SUPABASE_STORAGE_BUCKET,
            Key=asset_key
        )
        
        # Return the file as a streaming response
        return StreamingResponse(
            response['Body'],
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=signature.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Signature not found")

@router.post("/signature")
def upload_signature(file: UploadFile = File(...), org_id: str = Depends(get_current_org)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        s3_client = get_storage_client()
        asset_key = get_asset_key(org_id, "signature")
        
        # Read file content
        file_content = file.file.read()
        
        # Upload to Supabase storage
        s3_client.put_object(
            Bucket=settings.SUPABASE_STORAGE_BUCKET,
            Key=asset_key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        return {"detail": "Signature uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload signature: {str(e)}") 