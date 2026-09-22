from database import engine, Base
from models import Organization, User

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")