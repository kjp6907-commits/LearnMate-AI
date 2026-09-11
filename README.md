# 🎓 LearnMate AI

> **A Personalized AI Learning Tutor for UN Sustainable Development Goal 4: Quality Education.**

LearnMate AI is an educational chatbot designed to make personalized, high-quality tutoring accessible to students worldwide. It simplifies complex academic concepts, adapts explanations to the learner's knowledge level, offers real-world examples, checks for understanding, and provides interactive practice and quizzes.

---

## 📁 Project Architecture

```text
LearnMate-AI/
├── .streamlit/
│   └── config.toml     # Streamlit theme & server configuration
├── assets/
│   └── mascot.jpg      # AI tutor mascot visual asset
├── app.py              # Streamlit interactive web interface (Chat & Quiz modes)
├── api.py              # FastAPI REST backend service (/health, /chat)
├── gemini_service.py   # Reusable Gemini Flash integration & quiz generation
├── prompts.py          # Pedagogical system prompt definitions for SDG 4
├── test_gemini.py      # Diagnostic connectivity test script
├── test_qa_suite.py    # 15-category automated competition QA test suite
├── requirements.txt    # Project dependencies
├── .env                # Local environment secrets (ignored by Git)
├── .env.example        # Safe template for environment configuration
├── .gitignore          # Git exclusion rules
└── README.md           # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- A Google Gemini API key (obtainable from [Google AI Studio](https://aistudio.google.com/))

### 2. Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Open the `.env` file in the project root and add your Gemini API key:

```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

> ⚠️ **Security Note:** The `.env` file is listed in `.gitignore` to prevent exposing your API key. Never commit sensitive keys to source control.

---

### A. Run Diagnostic & Competition QA Tests
Verify API key connectivity or run the automated 15-category QA suite:

```bash
# Basic connection check
python test_gemini.py

# Full 15-category competition QA suite
python test_qa_suite.py
```

### B. Launch Streamlit Web UI
Run the interactive student tutor interface:

```bash
streamlit run app.py
```
This will open the web application in your browser (typically at `http://localhost:8501`).

### C. Launch FastAPI Backend Service
Run the external API service:

```bash
uvicorn api:app --reload --port 8000
```
- Interactive Swagger documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### 1. Health Check (`GET /health`)
Verify that the service is running:

```bash
curl http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

#### 2. Chat with Tutor (`POST /chat`)

**Request:**
- **Endpoint:** `POST http://localhost:8000/chat`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "message": "Explain photosynthesis in simple terms"
}
```

**Response (200 OK):**
```json
{
  "response": "Hello! Let's think of photosynthesis like plants baking their own food using sunlight...\n\nCheck Question: What do plants absorb from the air to make their food?"
}
```

#### Example using `curl` (Linux/macOS/Git Bash):
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Why is the sky blue?"}'
```

#### Example using PowerShell (Windows):
```powershell
$body = @{ message = "Why is the sky blue?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -ContentType "application/json" -Body $body
```

#### Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "What is the difference between speed and velocity?"}
)
print(response.json())
```

---

## 🎯 Target Core Capabilities (SDG 4 Roadmap)

1. **Simple Concept Explanations**: Break down academic topics into intuitive explanations.
2. **Adaptive Learning Levels**: Dynamically adjust depth for Beginner, Intermediate, or Advanced students.
3. **Real-world Examples**: Contextualize theory with concrete analogies and practical use cases.
4. **Comprehension Check Questions**: Automatically ask a quick question after explanations to ensure understanding.
5. **Practice Question Generator**: Create tailored problems across multiple academic subjects.
6. **Constructive Answer Feedback**: Evaluate student submissions with supportive, educational guidance.
7. **Interactive Quiz Mode**: Timed or multi-question assessment sessions.
8. **Educational Guardrails**: Keep dialogue focused on constructive learning and academic progress.
