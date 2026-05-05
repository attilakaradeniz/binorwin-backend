from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

# Security configurations (in production SECRET_KEY will be in a .env file!)
SECRET_KEY = "super_secret_temporary_key_for_binorwin"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Context for password hashing using bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# to verify if the provided plain password matches the hashed one in the database
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# to hash a plain password before saving it to the database
def get_password_hash(password):
    return pwd_context.hash(password)

# to generate a JWT (JSON Web Token) for the logged-in user
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    # Set the expiration time for the token
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    # Create the actual token string using the secret key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt