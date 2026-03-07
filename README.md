# AI-Driven Solar Inverter Failure Prediction & Intelligence Platform

A production-ready platform for predicting solar inverter shutdowns or underperformance using Machine Learning and providing operational insights via Generative AI.

## 🚀 Key Features

-   **Predictive Maintenance:** ML models (SCIKIT-LEARN) predict potential failures 7-10 days in advance.
-   **GenAI Insights:** Integrated AI engine (Gemini) provides natural language maintenance recommendations.
-   **Real-time Dashboard:** Operational dashboard showing live telemetry across multiple plants.
-   **Historical Analysis:** 7-day visualization of voltage, temperature, and power trends.
-   **AI Chatbot:** A non-blocking floating widget for querying plant data using RAG (Retrieval-Augmented Generation).

## 🛠 Tech Stack

-   **Frontend:** React, Chart.js, Vanilla CSS.
-   **Backend:** FastAPI (Python), Uvicorn.
-   **Database:** Supabase (PostgreSQL + REST API).
-   **AI/ML:** Scikit-learn, Google Gemini API, RAG Engine.
-   **DevOps:** Docker, Docker Compose.

## 📂 Project Structure

-   `/src`: React frontend components and pages.
-   `/backend`: FastAPI application logic.
    -   `/api`: REST endpoints.
    -   `/ml`: Machine learning prediction logic.
    -   `/genai`: LLM integration for maintenance insights.
    -   `/database`: Supabase client and caching.
    -   `/rag`: Retrieval-Augmented Generation engine.

## 🏁 Getting Started

### 1. Environment Setup
Create a `.env` file in the `backend/` directory based on `.env.example`:
```env
SUPABASE_URL=https://mughjkfscraxllgztswe.supabase.co
SUPABASE_KEY=sb_publishable_lCGawVQZUMOpiOHuscjlEw_BTYIyahb
GROK_API_KEY=your_api_key
```

### 2. Running with Docker (Recommended)
```bash
docker-compose up --build
```

### 3. Running Manually
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

**Frontend:**
```bash
npm install
npm start
```

## 📊 API Documentation
Once the backend is running, access the interactive Swagger UI at:
[http://localhost:8000/docs](http://localhost:8000/docs)

## 👥 Team Members

| Name | Phone | Email | College | Graduation Year |
|------|-------|-------|---------|-----------------|
| Heer Shah | 7600986367 | heershah3896@gmail.com | Nirma University | 2029 |
| Saud Topiwala | 7984709245 | 24bce263@nirmauni.ac.in | Nirma University | 2028 |
| Meer Patel | 9712705203 | 24bam042@nirmauni.ac.in | Nirma University | 2028 |
| Shrey Patel | 9328396580 | 24BCE250@nirmauni.ac.in | Nirma University | 2028 |
| Shubh Patel | 9512801279 | 24bam041@nirmauni.ac.in | Nirma University | 2028 |
