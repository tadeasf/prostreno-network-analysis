from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Base
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Set up the database engine and session
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

# Fetch a user
user = session.query(User).first()
print(user.description)  # print the current description

# Update the user
user.description = "New description"
print(session.is_modified(user))  # Should print True if the user is pending changes
session.add(user)
try:
    session.commit()
except Exception as e:
    print(e)


# Fetch the user again and print the updated description
user = session.query(User).first()
print(user.description)
