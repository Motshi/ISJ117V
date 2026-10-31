from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from app.database import users_collection
from app.models.user_models import (
    TokenResponse,
    UserLogin,
    UserOut,
    UserProfileUpdate,
    UserRegister,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


def _user_doc_to_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        full_name=doc["full_name"],
        email=doc["email"],
        phone_number=doc.get("phone_number"),
        location=doc.get("location"),
        minimum_match_score=doc.get("minimum_match_score"),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    user_doc = {
        "full_name": payload.full_name,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "phone_number": payload.phone_number,
        "location": payload.location,
    }
    try:
        result = await users_collection.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_doc["_id"] = result.inserted_id
    token = create_access_token({"sub": str(result.inserted_id)})
    return TokenResponse(access_token=token, user=_user_doc_to_out(user_doc))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    user_doc = await users_collection.find_one({"email": payload.email.lower()})
    if not user_doc or not verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user_doc["_id"])})
    return TokenResponse(access_token=token, user=_user_doc_to_out(user_doc))


@router.get("/profile", response_model=UserOut)
async def get_profile(current_user_id: str = Depends(get_current_user_id)):
    user_doc = await _get_user_or_404(current_user_id)
    return _user_doc_to_out(user_doc)


@router.put("/profile", response_model=UserOut)
async def update_profile(
    payload: UserProfileUpdate,
    current_user_id: str = Depends(get_current_user_id),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await users_collection.update_one({"_id": ObjectId(current_user_id)}, {"$set": updates})
    user_doc = await _get_user_or_404(current_user_id)
    return _user_doc_to_out(user_doc)


async def _get_user_or_404(user_id: str) -> dict:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
    user_doc = await users_collection.find_one({"_id": oid})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_doc
