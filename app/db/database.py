# Re-export database primitives so both app.db.database and app.core.database
# resolve to the same engine / session / Base objects.
from app.core.database import engine, SessionLocal, Base  # noqa: F401
