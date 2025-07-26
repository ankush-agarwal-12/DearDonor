from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api import auth, organizations, donors, donations, settings as settings_router, assets, export_import, receipts
from app.api.email import email_templates_router, receipts_email_router

settings = get_settings()

app = FastAPI(title="DearDonor Backend API", version="1.0.0")

# CORS setup (allow all for now, restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(donors.router)
app.include_router(donations.router)
app.include_router(settings_router.router)
app.include_router(assets.router)
app.include_router(export_import.router)
app.include_router(receipts.router)
app.include_router(email_templates_router)
app.include_router(receipts_email_router)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"} 