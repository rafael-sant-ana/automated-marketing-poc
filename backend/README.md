
Pa

---

-- Create the flows table
CREATE TABLE flows (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    instruction TEXT NOT NULL,
    hourInDay INT NOT NULL,
    minuteInDay INT NOT NULL,
    occurrences VARCHAR(50) DEFAULT 'dayToDay',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the receivers table
CREATE TABLE receivers (
    id SERIAL PRIMARY KEY,
    flow_id INT REFERENCES flows(id) ON DELETE CASCADE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


3. Local Project Setup
Clone the repository (or download the files).
Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`


Install dependencies:
pip install -r requirements.txt


Create a .env file:
Create a file named .env in the root directory.
Copy the contents from .env.example or add the following, replacing the placeholders with your Supabase credentials:
SUPABASE_URL="YOUR_SUPABASE_URL"
SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"


4. Run the Application
Run the FastAPI server using Uvicorn:
uvicorn main:app --reload

When creating a flow, the reference timezone will be your computer's timezone, not UTC.
