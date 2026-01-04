import uuid
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from backend.database.database import DB_SESSION
import backend.database.models as models
import backend.database.schemas as schemas
from backend.helpers.get_current_user import CURRENT_USER
from backend.helpers.credentials import hash_password, verify_password, compare_ids

router = APIRouter(
    prefix="/users", tags=["users"]
)


@router.get(
    "/", response_model=list[schemas.UserDisplay], status_code=status.HTTP_200_OK
)
async def get_all(db: DB_SESSION):
    result = await db.scalars(select(models.User))
    users = result.all()
    return users


@router.get("/{id}", response_model=schemas.UserDisplay, status_code=status.HTTP_200_OK)
async def get_one(id: int, db: DB_SESSION):
    user = await db.get(models.User, id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post(
    "/", response_model=schemas.UserDisplay, status_code=status.HTTP_201_CREATED
)
async def create(request: schemas.UserRegister, db: DB_SESSION):
    user = await db.scalar(
        select(models.User).where(models.User.email == request.email)
    )
    if not user:
        hashed_password = hash_password(request.password.get_secret_value())
        new_user = models.User(
            username=request.username, email=request.email, password=hashed_password
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    else:
        raise HTTPException(
            status_code=status.HTTP_226_IM_USED, detail="User already exists"
        )


@router.put(
    "/{id}", response_model=schemas.UserDisplay, status_code=status.HTTP_202_ACCEPTED
)
async def change_password(
    id: int,
    current_user: CURRENT_USER,
    request: schemas.UserChangePassword,
    db: DB_SESSION,
):
    compare_ids(current_user.id, id)

    user = await db.get(models.User, id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    old_password_plain = request.old_password.get_secret_value()
    new_password_plain = request.new_password.get_secret_value()
    if not verify_password(old_password_plain, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect old password"
        )

    user.password = hash_password(new_password_plain)
    user.token_version = uuid.uuid4()

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{id}")
async def delete(id: int, current_user: CURRENT_USER, db: DB_SESSION):
    compare_ids(current_user.id, id)
    user = await db.get(models.User, id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await db.delete(user)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
