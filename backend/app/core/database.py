from sqlmodel import SQLModel, create_engine

from app.core.config import settings

# Create an engine using the configured DATABASE_URL and expose SQLModel as Base
engine = create_engine(str(settings.DATABASE_URL), echo=settings.DEBUG)

# For compatibility with code which expects a 'Base' with metadata
Base = SQLModel

def init_db() -> None:
    """Create DB tables (if they don't exist). Call during startup."""
    SQLModel.metadata.create_all(bind=engine)

    # Create default superuser if missing
    try:
        from sqlmodel import Session, select
        from app.crud import get_user_by_email, create_user

        with Session(engine) as session:
            if settings.FIRST_SUPERUSER:
                existing = get_user_by_email(session, settings.FIRST_SUPERUSER)
                if not existing:
                    create_user(session, username=settings.FIRST_SUPERUSER.split("@")[0], email=settings.FIRST_SUPERUSER, password=settings.FIRST_SUPERUSER_PASSWORD, is_superuser=True)
    except Exception:
        # don't crash if DB isn't ready for queries during early startup
        pass