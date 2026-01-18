"""
Cortex - User Profile Models
"""

from typing import List, Optional
from pydantic import BaseModel

class UserProfileBase(BaseModel):
    name: str = "User"
    role: Optional[str] = None
    bio: Optional[str] = None
    traits: List[str] = []

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
