from sqlalchemy.orm import Session
from database.models.accounts import UserModel, UserProfileModel
from security.passwords import hash_password

def get_user_by_id(db: Session, user_id: int):
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()

def create_user(db: Session, email: str, raw_password: str, group_id: int):
    user = UserModel.create(email=email, raw_password=raw_password, group_id=group_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_email(db: Session, user: UserModel, new_email: str):
    user.email = new_email
    db.commit()
    db.refresh(user)
    return user

def deactivate_user(db: Session, user: UserModel):
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: UserModel):
    db.delete(user)
    db.commit()
