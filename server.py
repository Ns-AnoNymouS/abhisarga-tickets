from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
import dotenv
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os

dotenv.load_dotenv()
templates = Jinja2Templates(directory="templates")

# Secret key and algorithm for JWT
token_secret = os.getenv("JWT_SECRET_KEY", "your_secret_key")

token_algorithm = "HS256"
token_expire_minutes = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# MongoDB setup
database_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
client = MongoClient(database_url)
db = client["abhisarga"]
users_collection = db["users"]
tickets_collection = db["tickets"]

# FastAPI instance
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_user(username: str):
    return users_collection.find_one({"username": username})

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, token_secret, algorithm=token_algorithm)

def get_ticket(ticket_number: str):
    return tickets_collection.find_one({"ticket": ticket_number})

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "title": "Home Page"}
    )

@app.get("/scan")
def scan(request: Request):
    return templates.TemplateResponse(
        "scan.html", {"request": request, "title": "Home Page"}
    )

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = get_user(form_data.username)
        if not user or not verify_password(form_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=timedelta(minutes=token_expire_minutes),
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/user")
def user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if user:
        raise HTTPException(status_code=409, detail="User already exists")
    users_collection.insert_one(
        {
            "username": form_data.username,
            "password": pwd_context.hash(form_data.password),
        }
    )
    user = get_user(form_data.username)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/details")
def protected_route(
    request: Request,
    ticket_number: str = Query(...),
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = jwt.decode(token, token_secret, algorithms=[token_algorithm])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        ticket_details = get_ticket(ticket_number)
        if ticket_details and "_id" in ticket_details:
            del ticket_details["_id"]

        return {
            "user": username,
            "ticket": ticket_details,
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

class RegisterRequest(BaseModel):
    name: str
    phone: str
    code: str

@app.post("/register")
def register(request: RegisterRequest, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, token_secret, algorithms=[token_algorithm])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid Token")

        ticket_details = get_ticket(request.code)

        tickets_collection.insert_one(
            {
                "soldby": username,
                "name": request.name,
                "phone": request.phone,
                "ticket": request.code,
            }
        )
        return {"message": "User registered successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
