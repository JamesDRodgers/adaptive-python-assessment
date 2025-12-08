# Quick Installation Guide

## For Local Development

### Step 1: Navigate to Backend
```bash
cd adaptive_python_assessment/backend
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

**Option A: Create .env file (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here
```

**Option B: Set environment variables directly**

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
set ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"
```

### Step 4: Start the Backend Server
```bash
uvicorn app:app --reload
```

You should see:
```
INFO:     Session cleanup thread started
INFO:     OpenAI API connection validated successfully
INFO:     API startup complete - ready to accept requests
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 5: Open the Frontend

**Option A: Direct File Open**
- Navigate to `frontend/` folder
- Double-click `index.html`

**Option B: HTTP Server (Recommended)**
```bash
cd ../frontend
python -m http.server 3000
```

Then open: http://localhost:3000

### Step 6: Test the Application
1. The assessment should start automatically
2. Answer a question and submit
3. Verify you receive feedback and the next question

---

## For Production Deployment

### Render.com

1. Create new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ALLOWED_ORIGINS`: Your frontend URL(s)

### Railway.app

1. Create new project
2. Connect repository
3. Add environment variables in Variables tab:
   - `OPENAI_API_KEY`
   - `ALLOWED_ORIGINS`
4. Deploy

### Fly.io

```bash
# Login
fly auth login

# Set secrets
fly secrets set OPENAI_API_KEY=sk-your-key
fly secrets set ALLOWED_ORIGINS=https://yourdomain.com

# Deploy
fly deploy
```

### Heroku

```bash
# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set ALLOWED_ORIGINS=https://yourdomain.com

# Deploy
git push heroku main
```

---

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
- Make sure you've set the environment variable
- For `.env` file, ensure it's in the `/backend` directory
- Restart the server after setting environment variables

### "ModuleNotFoundError: No module named 'fastapi'"
- Run `pip install -r requirements.txt` in the backend directory
- Make sure you're in the correct directory

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Add frontend URL to `ALLOWED_ORIGINS`

### Session expires immediately
- This is expected after 1 hour of inactivity
- Just start a new assessment

---

## Verification Checklist

After installation, verify:
- [ ] Backend starts without errors
- [ ] See "OpenAI API connection validated successfully" in logs
- [ ] Frontend loads and shows first question
- [ ] Can submit answers and receive feedback
- [ ] Health check works: http://localhost:8000/health
- [ ] API docs work: http://localhost:8000/docs

---

## Getting Help

If you encounter issues:
1. Check the logs for error messages
2. Review the full README.md
3. Verify all environment variables are set correctly
4. Ensure your OpenAI API key is valid and has credit
5. Check that all dependencies are installed
