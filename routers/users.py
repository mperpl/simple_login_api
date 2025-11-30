import uuid
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from database import DB_SESSION
import models
from routers.utils import check_credentials
import schemas
from security import CURRENT_USER, hash_password, verify_password

router = APIRouter(
    prefix='/users',
    tags=['users (to authorise use email not username)']
)

@router.get('/', response_model=list[schemas.UserDisplay], status_code=status.HTTP_200_OK)
def get_all(db: DB_SESSION):
    users = db.scalars(select(models.User)).all()
    if not users: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Users not found')
    return users

@router.get('/{id}', response_model=schemas.UserDisplay, status_code=status.HTTP_200_OK)
def get_one(id: int, db: DB_SESSION):
    user = db.get(models.User, id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return user

@router.post('/', response_model=schemas.UserDisplay, status_code=status.HTTP_201_CREATED)
def create(request: schemas.UserRegister, db: DB_SESSION):
    user = db.scalar(select(models.User.email == request.email))
    if not user:  
        hashed_password = hash_password(request.password.get_secret_value())
        new_user = models.User(username=request.username, email=request.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    else:
        raise HTTPException(status_code=status.HTTP_226_IM_USED, detail="User already exists.")
    

@router.put('/{id}', response_model=schemas.UserDisplay, status_code=status.HTTP_202_ACCEPTED)
def change_password(id: int, current_user: CURRENT_USER, request: schemas.UserChangePassword, db: DB_SESSION):
    user = db.get(models.User, id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    check_credentials(current_user.id, user.id)

    old_password_plain = request.old_password.get_secret_value()
    new_password_plain = request.new_password.get_secret_value()

    if not verify_password(old_password_plain, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect old password.')

    user.password = hash_password(new_password_plain)

    user.token_version = uuid.uuid4()

    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.delete('/{id}')
def delete(id: int, current_user: CURRENT_USER, db: DB_SESSION):
    user = db.get(models.User, id)
    refresh_token = db.scalar(select(models.RefreshToken).where(models.RefreshToken.user_id == user.id))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    check_credentials(current_user.id, user.id)

    db.delete(user)
    db.delete(refresh_token)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
