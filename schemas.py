"""
Database Schemas for MRM Cybersecurity Hub

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., Tool -> "tool").
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal
from datetime import datetime

class Tool(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Short description")
    category: Literal[
        "Reconnaissance", "Exploitation", "Forensics", "Web Security", "Wireless", "OSINT"
    ]
    tags: List[str] = Field(default_factory=list)
    popularity: int = Field(0, ge=0, description="Relative popularity score")
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    link: Optional[HttpUrl] = None

class Course(BaseModel):
    title: str
    thumbnail: Optional[HttpUrl] = None
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    slug: str
    description: Optional[str] = None

class Lab(BaseModel):
    title: str
    category: Literal["Beginner", "Intermediate", "Advanced"]
    estimated_minutes: int = Field(..., ge=5, le=240)
    link: Optional[HttpUrl] = None
    score: int = Field(0, ge=0)

class Incident(BaseModel):
    country: str
    type: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    time: datetime
    description: Optional[str] = None
    mitre_attack_vector: Optional[str] = None

class Podcast(BaseModel):
    title: str
    audio_url: Optional[HttpUrl] = None
    youtube_url: Optional[HttpUrl] = None
    guest: Optional[str] = None
    published_at: Optional[datetime] = None

class ContactMessage(BaseModel):
    name: str
    email: str
    message: str

class Subscriber(BaseModel):
    email: str
    source: Optional[str] = "website"

class User(BaseModel):
    name: str
    email: str
    password_hash: str
    is_active: bool = True
