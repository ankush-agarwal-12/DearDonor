import os
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.donor import Donor
from app.models.donation import Donation
from app.core.security import get_current_org
from uuid import UUID

router = APIRouter(prefix="/export", tags=["Export/Import"])

EXPORTS_BASE = "uploads/organizations"

def get_export_path(org_id: str, filename: str) -> str:
    # Create temporary file path without storing permanently
    import tempfile
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, filename)

def make_df_excel_safe(df):
    for col in df.select_dtypes(include=['datetimetz']).columns:
        df[col] = df[col].dt.tz_localize(None)
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].apply(lambda x: hasattr(x, 'tzinfo')).any():
            df[col] = df[col].apply(lambda x: x.replace(tzinfo=None) if hasattr(x, 'tzinfo') and x.tzinfo else x)
    return df

@router.get("/donors")
def export_donors(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    donors = db.query(Donor).filter(Donor.organization_id == org_id).all()
    df = pd.DataFrame([d.__dict__ for d in donors])
    df = df.drop("_sa_instance_state", axis=1, errors="ignore")
    df = make_df_excel_safe(df)
    path = get_export_path(org_id, "donors_export.xlsx")
    df.to_excel(path, index=False)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="donors_export.xlsx")

@router.get("/donations")
def export_donations(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    donations = db.query(Donation).filter(Donation.organization_id == org_id).all()
    df = pd.DataFrame([d.__dict__ for d in donations])
    df = df.drop("_sa_instance_state", axis=1, errors="ignore")
    df = make_df_excel_safe(df)
    path = get_export_path(org_id, "donations_export.xlsx")
    df.to_excel(path, index=False)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="donations_export.xlsx")

@router.post("/import/donors")
def import_donors(file: UploadFile = File(...), db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    if file.content_type not in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if file.content_type == "text/csv":
        df = pd.read_csv(file.file)
    else:
        df = pd.read_excel(file.file)
    for _, row in df.iterrows():
        donor = Donor(
            organization_id=org_id,
            full_name=row.get("full_name", ""),
            email=row.get("email", ""),
            phone=row.get("phone"),
            address=row.get("address"),
            pan=row.get("pan"),
            donor_type=row.get("donor_type", "Individual")
        )
        db.add(donor)
    db.commit()
    return {"detail": "Donors imported successfully"}

@router.post("/import/donations")
def import_donations(file: UploadFile = File(...), db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    if file.content_type not in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if file.content_type == "text/csv":
        df = pd.read_csv(file.file)
    else:
        df = pd.read_excel(file.file)
    for _, row in df.iterrows():
        donation = Donation(
            organization_id=org_id,
            donor_id=row.get("donor_id"),
            amount=row.get("amount"),
            date=row.get("date"),
            purpose=row.get("purpose"),
            payment_mode=row.get("payment_mode"),
            payment_details=row.get("payment_details", {}),
            receipt_path=row.get("receipt_path"),
            email_sent=row.get("email_sent", False),
            whatsapp_sent=row.get("whatsapp_sent", False)
        )
        db.add(donation)
    db.commit()
    return {"detail": "Donations imported successfully"} 