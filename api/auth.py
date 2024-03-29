import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from db.models import User, Post
from core.database import get_db
from .schemas import UserRegistration, UserLogin, UserProfile, PostWithAuthorResponse
from core.security import verify_password, create_access_token, decode_access_token, get_password_hash


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

@router.get('/curent_profile/', response_model=UserProfile, tags=['users'])
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    decoded_token = decode_access_token(token)
    if decoded_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user_id = decoded_token.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@router.get('/profile/{user_id}', response_model=UserProfile, tags=['users'])
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='Профиль пользователя не найден')
    return user


EMAILHUNTER_API_KEY = 'c2d53c62117c318284efadbd769f23c450500117'
@router.post('/auth/register/', response_model=UserProfile, tags=['auth'])
def register(user: UserRegistration, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username already taken')

    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')

    emailhunter_url = f'https://api.hunter.io/v2/email-verifier?email={user.email}&api_key={EMAILHUNTER_API_KEY}'
    response = requests.get(emailhunter_url)
    emailhunter_data = response.json()

    if emailhunter_data.get('data', {}).get('result') != 'valid':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email does not exist')

    new_user = User(username=user.username, email=user.email, full_name=user.full_name)
    new_user.password = get_password_hash(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post('/auth/login', tags=['auth'])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')

    access_token = create_access_token(user.id)
    return {'access_token': access_token, 'token_type': 'Bearer'}



