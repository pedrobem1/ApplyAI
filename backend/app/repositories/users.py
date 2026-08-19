from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User

DEMO_USER_EMAIL = "demo@applyai.local"


def get_or_create_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is not None:
        return user

    user = User(email=DEMO_USER_EMAIL)
    db.add(user)
    db.flush()
    return user

