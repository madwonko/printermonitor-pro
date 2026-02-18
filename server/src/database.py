"""
Database Connection and Session Management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    echo=settings.ENVIRONMENT == "development",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_timescaledb():
    """Initialize TimescaleDB extension"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.execute(text("""
                SELECT create_hypertable(
                    'printer_metrics', 
                    'timestamp',
                    if_not_exists => TRUE
                );
            """))
            conn.commit()
            print("✓ TimescaleDB extension initialized")
            print("✓ printer_metrics converted to hypertable")
    except Exception as e:
        print(f"⚠ TimescaleDB initialization skipped: {e}")


def init_db():
    """Initialize database - creates tables and seeds data"""
    # Import all models
    from .models import User, ProxyDevice, Printer, PrinterMetrics, LicenseTier, License
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Initialize TimescaleDB
    init_timescaledb()
    
    # Seed license tiers
    from .utils.seed_licenses import seed_license_tiers
    db = SessionLocal()
    try:
        seed_license_tiers(db)
    finally:
        db.close()
