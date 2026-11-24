from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , declarative_base 


engine = create_engine(
    settings.database_url
)

SessionLocal=sessionmaker(
    bind=engine , 
    autocommit=False,
    autoflush=False)


Base = declarative_base()



