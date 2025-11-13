import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone

from database import db, create_document, get_documents
from schemas import Tool, Course, Lab, Incident, Podcast, ContactMessage, Subscriber

app = FastAPI(title="MRM Cybersecurity API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsItem(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None

@app.get("/")
def root():
    return {"name": "MRM Cybersecurity API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "❌ Unknown"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Seed minimal content if needed
@app.post("/seed")
def seed():
    try:
        # Only seed if empty
        if db is None:
            raise HTTPException(500, "Database not configured")
        if db["tool"].count_documents({}) == 0:
            create_document("tool", Tool(name="Nmap", description="Network exploration tool and security / port scanner.", category="Reconnaissance", tags=["network", "scanner"], popularity=95, difficulty="Intermediate", link="https://nmap.org").model_dump())
            create_document("tool", Tool(name="Wireshark", description="Network protocol analyzer.", category="Forensics", tags=["packet", "analyzer"], popularity=90, difficulty="Beginner", link="https://www.wireshark.org").model_dump())
        if db["course"].count_documents({}) == 0:
            create_document("course", Course(title="Ethical Hacking Basics", difficulty="Beginner", slug="ethical-hacking-basics", description="Kickstart into ethical hacking.").model_dump())
            create_document("course", Course(title="Linux for Hackers", difficulty="Beginner", slug="linux-for-hackers").model_dump())
        if db["lab"].count_documents({}) == 0:
            create_document("lab", Lab(title="Intro Recon Lab", category="Beginner", estimated_minutes=20, score=0).model_dump())
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, str(e))

# Basic endpoints for tools and courses (read-only for now)
@app.get("/tools")
def list_tools(q: Optional[str] = None, category: Optional[str] = None, sort: Optional[str] = None):
    if db is None:
        return []
    filter_dict = {}
    if q:
        filter_dict["name"] = {"$regex": q, "$options": "i"}
    if category:
        filter_dict["category"] = category
    tools = list(db["tool"].find(filter_dict))
    for t in tools:
        t["_id"] = str(t["_id"]) 
    if sort == "popularity":
        tools.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif sort == "difficulty":
        diff_order = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}
        tools.sort(key=lambda x: diff_order.get(x.get("difficulty", "Beginner"), 0))
    elif sort == "category":
        tools.sort(key=lambda x: x.get("category", ""))
    return tools

@app.get("/courses")
def list_courses():
    if db is None:
        return []
    courses = list(db["course"].find({}))
    for c in courses:
        c["_id"] = str(c["_id"]) 
    return courses

# News proxy endpoint (reads from external APIs if key present, else returns sample)
@app.get("/news", response_model=List[NewsItem])
def get_news():
    api_key = os.getenv("NEWSDATA_API_KEY") or os.getenv("NEWSAPI_KEY")
    items: List[NewsItem] = []
    if api_key:
        try:
            import requests
            # Try NewsData.io
            url = f"https://newsdata.io/api/1/latest?apikey={api_key}&q=cybersecurity&country=us,gb,ca&language=en"
            r = requests.get(url, timeout=8)
            data = r.json()
            for a in (data.get("results") or [])[:12]:
                items.append(NewsItem(
                    title=a.get("title") or "Untitled",
                    description=a.get("description"),
                    url=a.get("link") or a.get("url") or "",
                    image_url=a.get("image_url") or a.get("image_url") or None,
                    source=a.get("source_id"),
                    published_at=a.get("pubDate") or a.get("pubDate")
                ))
        except Exception:
            pass
    if not items:
        # fallback sample
        now = datetime.now(timezone.utc).isoformat()
        items = [
            NewsItem(title="Latest CVE trends show rise in supply-chain attacks", url="https://thehackernews.com/", source="Sample", published_at=now),
            NewsItem(title="Krebs: Major ISP suffers DDoS impacting services", url="https://krebsonsecurity.com/", source="Sample", published_at=now),
            NewsItem(title="ThreatPost: Critical bug patched in popular router firmware", url="https://threatpost.com/", source="Sample", published_at=now),
        ]
    return items

# Simple incidents demo (would normally come from external feeds)
@app.get("/incidents")
def incidents():
    now = datetime.now(timezone.utc)
    sample = [
        {
            "country": "US", "type": "DDoS", "severity": "High", "time": now.isoformat(),
            "description": "Large-scale DDoS on hosting provider.", "mitre_attack_vector": "T1498"
        },
        {
            "country": "DE", "type": "Malware", "severity": "Medium", "time": now.isoformat(),
            "description": "Emotet activity resurgence.", "mitre_attack_vector": "T1204"
        },
        {
            "country": "IN", "type": "Phishing", "severity": "Low", "time": now.isoformat(),
            "description": "Targeted phishing campaign detected.", "mitre_attack_vector": "T1566"
        },
    ]
    return sample

# Newsletter subscription and contact endpoints
@app.post("/subscribe")
def subscribe(sub: Subscriber):
    if db is None:
        return {"status": "disabled"}
    create_document("subscriber", sub)
    return {"status": "ok"}

@app.post("/contact")
def contact(msg: ContactMessage):
    if db is None:
        return {"status": "disabled"}
    create_document("contactmessage", msg)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
