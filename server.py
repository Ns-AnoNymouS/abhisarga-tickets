from datetime import datetime, timedelta
import os
import json

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from pymongo import MongoClient
from pydantic import BaseModel
import jwt
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# CORS Middleware (Adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
TOKEN_SECRET = os.getenv("JWT_SECRET_KEY", "your_secret_key")
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 3000

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Authentication Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# MongoDB Connection
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
client = MongoClient(DATABASE_URL)
db = client["abhisarga"]
users_collection = db["users"]
tickets_collection = db["tickets"]

# Admin Credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# Helper Functions
def get_user(username: str):
    """Fetch a user from the database by username."""
    return users_collection.find_one({"username": username})


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a given password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, TOKEN_SECRET, algorithm=TOKEN_ALGORITHM)


def decode_token(token: str):
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, TOKEN_SECRET, algorithms=[TOKEN_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_ticket(ticket_number: str):
    """Fetch a ticket from the database by ticket number."""
    return tickets_collection.find_one({"ticket": ticket_number})


def update_ticket(ticket_number: str, update_data: dict):
    """Update a ticket with the provided data."""
    tickets_collection.update_one({"ticket": ticket_number}, {"$set": update_data})


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class RegisterRequest(BaseModel):
    name: str
    phone: str
    code: str


# Routes
@app.get("/")
def home(request: Request):
    """Render the login page."""
    return templates.TemplateResponse(
        "login.html", {"request": request, "title": "Home Page"}
    )


@app.get("/scan")
def scan_page(request: Request):
    """Render the scan page."""
    return templates.TemplateResponse(
        "scan.html", {"request": request, "title": "Scan Ticket"}
    )


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return a JWT token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/user")
async def create_user(request: Request):
    """Create a new user with admin verification and return JWT token."""
    try:
        body = await request.json()
        admin_username = body.get("admin_username")
        admin_password = body.get("admin_password")
        new_username = body.get("new_username")
        new_password = body.get("new_password")

        # Validate admin credentials
        if admin_username != ADMIN_USERNAME or admin_password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")

        # Check if user already exists
        if get_user(new_username):
            raise HTTPException(status_code=409, detail="User already exists")

        # Hash the new user's password
        hashed_password = pwd_context.hash(new_password)
        users_collection.insert_one(
            {"username": new_username, "password": hashed_password}
        )

        # Generate JWT token for new user
        access_token = create_access_token(
            data={"sub": new_username},
            expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        )

        return {
            "message": "User created successfully",
            "access_token": access_token,
            "token_type": "bearer",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/details")
def get_ticket_details(
    request: Request,
    ticket_number: str = Query(...),
    token: str = Depends(oauth2_scheme),
):
    """Retrieve details of a ticket after verifying the user token."""
    username = decode_token(token)

    ticket_details = get_ticket(ticket_number)
    if not ticket_details:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Remove MongoDB ObjectId before returning
    ticket_details.pop("_id", None)

    return {
        "user": username,
        "ticket": ticket_details if ticket_details.get("name") else None,
    }


@app.post("/register")
def register_ticket(request: RegisterRequest, token: str = Depends(oauth2_scheme)):
    """Register a user to a ticket after authentication."""
    username = decode_token(token)

    if not get_ticket(request.code):
        raise HTTPException(status_code=404, detail="Invalid ticket code")

    update_ticket(
        request.code, {"soldby": username, "name": request.name, "phone": request.phone}
    )

    return {"message": "User registered successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
