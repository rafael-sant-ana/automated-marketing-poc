import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from models import UserCreate, User, FlowCreate, Flow, ReceiverCreate, Receiver
from scheduler import schedule_flow, scheduler

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in the .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("Scheduler started...")

    flows = supabase.table('flows').select("*").execute()
    flows = flows.data

    for flow in flows:
        schedule_flow(
            flow_id=flow['id'],
            hour=flow['hourInDay'],
            minute=flow['minuteInDay'],
            instruction=flow['instruction']
        )
    print("Scheduler populated...")


    yield

    
    scheduler.shutdown()
    print("Scheduler stopped.")

app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_email_body(instruction: str) -> str:
    print(f"Generating email body for instruction: '{instruction}'")
    return f"Hello, this is your daily update based on: '{instruction}'. Have a great day!"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates token and returns user data from Supabase."""
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {e}")

@app.post("/signup", response_model=User)
async def signup(user_credentials: UserCreate):
    """Creates a new user account in Supabase."""
    try:
        user_response = supabase.auth.sign_up({
            "email": user_credentials.email,
            "password": user_credentials.password,
        })
        if not user_response.user:
            raise HTTPException(status_code=400, detail="Could not create user. User may already exist.")
        
        return User(id=user_response.user.id, email=user_response.user.email)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Logs in a user and returns an access token."""
    try:
        session_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        print(session_response)
        if not session_response.session:
             raise HTTPException(status_code=400, detail="Incorrect email or password")

        return {"access_token": session_response.session.access_token, "token_type": "bearer"}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/integrate/gmail")
async def integrate_gmail(current_user: User = Depends(get_current_user)):
    """Placeholder for Gmail OAuth integration."""
    return {"message": "This endpoint would initiate the Gmail OAuth flow.", "user_id": current_user.id}


@app.post("/flows", response_model=Flow)
async def create_flow(flow_data: FlowCreate, current_user: User = Depends(get_current_user)):
    """Creates a new flow for the authenticated user."""
    try:
        flow_dict = flow_data.dict()
        flow_dict['user_id'] = current_user.id
        
        response = supabase.table('flows').insert(flow_dict).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create flow")

        created_flow = response.data[0]
        
        schedule_flow(
            flow_id=created_flow['id'],
            hour=created_flow['hourInDay'],
            minute=created_flow['minuteInDay'],
            instruction=created_flow['instruction']
        )
        
        return Flow(**created_flow)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/flows", response_model=List[Flow])
async def get_flows(current_user: User = Depends(get_current_user)):
    """Retrieves all flows for the authenticated user."""
    try:
        response = supabase.table('flows').select("*").eq('user_id', current_user.id).execute()
        return [Flow(**flow) for flow in response.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/receivers", response_model=Receiver)
async def add_receiver_to_flow(receiver_data: ReceiverCreate, current_user: User = Depends(get_current_user)):
    """Adds a new receiver to a specific flow."""
    try:
        flow_response = supabase.table('flows').select("id").eq('id', receiver_data.flow_id).eq('user_id', current_user.id).execute()
        if not flow_response.data:
            raise HTTPException(status_code=404, detail="Flow not found or you don't have permission.")

        receiver_dict = receiver_data.dict()
        response = supabase.table('receivers').insert(receiver_dict).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create receiver")
            
        return Receiver(**response.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/flows/{flow_id}/receivers", response_model=List[Receiver])
async def get_receivers_for_flow(flow_id: int, current_user: User = Depends(get_current_user)):
    """Retrieves all receivers for a specific flow."""
    try:
        flow_response = supabase.table('flows').select("id").eq('id', flow_id).eq('user_id', current_user.id).execute()
        if not flow_response.data:
            raise HTTPException(status_code=404, detail="Flow not found or you don't have permission.")

        response = supabase.table('receivers').select("*").eq('flow_id', flow_id).execute()
        return [Receiver(**receiver) for receiver in response.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Welcome to the Email Flow API"}
