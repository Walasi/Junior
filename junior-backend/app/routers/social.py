from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.friend import Friendship, Group, GroupMember
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/social", tags=["Social"])

class FriendRequest(BaseModel):
    friend_username: str

class FriendOut(BaseModel):
    id: int
    username: str
    status: str

    class Config:
        from_attributes = True

@router.post("/friend/request")
def send_friend_request(
    req: FriendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    friend = db.query(User).filter(User.username == req.friend_username).first()
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")
    if friend.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    existing = db.query(Friendship).filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend.id)) |
        ((Friendship.user_id == friend.id) & (Friendship.friend_id == current_user.id))
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already exists")
    new_req = Friendship(user_id=current_user.id, friend_id=friend.id, status="pending")
    db.add(new_req)
    db.commit()
    return {"message": f"Friend request sent to {friend.username}"}

@router.get("/friend/requests")
def get_friend_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requests = db.query(Friendship).filter(
        Friendship.friend_id == current_user.id,
        Friendship.status == "pending"
    ).all()
    result = []
    for req in requests:
        requester = db.query(User).get(req.user_id)
        result.append({"id": req.id, "username": requester.username})
    return result

@router.post("/friend/accept/{request_id}")
def accept_friend(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(Friendship).filter(Friendship.id == request_id, Friendship.friend_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "accepted"
    db.commit()
    return {"message": "Friend accepted"}

@router.get("/friends", response_model=List[FriendOut])
def list_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    friendships = db.query(Friendship).filter(
        ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)),
        Friendship.status == "accepted"
    ).all()
    friends = []
    for f in friendships:
        friend_id = f.friend_id if f.user_id == current_user.id else f.user_id
        friend = db.query(User).get(friend_id)
        friends.append({"id": friend.id, "username": friend.username, "status": "accepted"})
    return friends


class GroupCreate(BaseModel):
    name: str
    member_usernames: List[str] = []

@router.post("/group")
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_group = Group(name=group.name, created_by=current_user.id)
    db.add(new_group)
    db.flush()
    # Add creator as admin
    admin = GroupMember(group_id=new_group.id, user_id=current_user.id, role="admin")
    db.add(admin)
    for username in group.member_usernames:
        user = db.query(User).filter(User.username == username).first()
        if user and user.id != current_user.id:
            member = GroupMember(group_id=new_group.id, user_id=user.id)
            db.add(member)
    db.commit()
    return {"group_id": new_group.id, "name": new_group.name}

@router.get("/groups")
def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    groups = []
    for m in memberships:
        group = db.query(Group).get(m.group_id)
        groups.append({"id": group.id, "name": group.name, "role": m.role})
    return groups