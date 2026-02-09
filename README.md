# 🤖 Agentic Learning Copilot

**AI-Based Adaptive Assessment and Remedial Learning System for Programming Education**

A research-grade MVP implementing a multi-agent adaptive learning system with misconception diagnosis, personalized content generation, and comprehensive analytics.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Groq API key for real LLM

### One-Command Setup

```bash
# Clone and setup
cd agentic-copilot

# Backend
cd backend
pip install -r requirements.txt
# Edit .env if using Groq (LLM_MODE=groq)
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access
- **Student Portal**: http://localhost:5173
- **Instructor Dashboard**: http://localhost:5173/instructor/login (credentials: `instructor` / `teach123`)
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
agentic-copilot/
├── backend/
│   ├── app/
│   │   ├── agents/          # Multi-agent system
│   │   │   ├── diagnostic.py     # Misconception detection
│   │   │   ├── content.py        # Micro-lesson generation
│   │   │   ├── assessment.py     # Question generation
│   │   │   ├── verifier.py       # Quality verification
│   │   │   ├── orchestrator.py   # Learning loop control
│   │   │   └── teacher_support.py # Instructor analytics
│   │   ├── api/             # FastAPI routes
│   │   ├── db/              # SQLModel database
│   │   ├── llm/             # LLM provider system
│   │   ├── metrics/         # Research metrics
│   │   └── sandbox/         # Safe code execution
│   └── tests/               # Pytest tests
├── frontend/                # React + TypeScript UI
├── data/seed/               # Initial content
└── scripts/                 # Experiment runner
```

## Features

### Multi-Agent System
| Agent | Role |
|-------|------|
| **Orchestrator** | Manages adaptive learning loop |
| **Diagnostic** | Identifies student misconceptions |
| **Content** | Generates personalized micro-lessons |
| **Assessment** | Creates MCQ and coding questions |
| **Verifier** | Validates generated content |
| **TeacherSupport** | Provides instructor analytics |

### Student Flow
1. **Login** → Register with baseline level
2. **Pretest** → Initial assessment
3. **Adaptive Loop** → TEACH → TEST → (RETEACH/ADVANCE)
4. **Progress** → View mastery dashboard
5. **Posttest** → Final assessment

### LLM Modes
```bash
# Mock mode (no API key needed)
LLM_MODE=mock

# Groq mode (requires API key)
LLM_MODE=groq
GROQ_API_KEY=your_key_here
```

## API Endpoints

**Auth**
- `POST /api/auth/login` - Student login/register
- `POST /api/auth/instructor/login` - Instructor login

**Learning**
- `GET /api/pretest` - Get pretest questions
- `POST /api/pretest/submit` - Submit pretest
- `GET /api/learn/{student_id}` - Get next content
- `POST /api/attempt` - Submit question attempt
- `GET /api/progress/{student_id}` - Get progress

**Instructor**
- `GET /api/instructor/dashboard` - Analytics overview
- `GET /api/instructor/students/{id}` - Student details
- `GET /api/instructor/export/metrics` - Research metrics

## Run Experiment

```bash
cd scripts
python run_experiment.py --control 50 --experimental 50 --iterations 20
```

Outputs:
- `data/exports/experiment_results.json`
- `data/exports/experiment_logs.csv`

## Research Metrics

- **Item Analysis**: p-value (difficulty), discrimination index
- **Pre-Post**: Improvement, Cohen's d effect size
- **Diagnostic**: Precision, recall, Cohen's kappa
- **Equity**: Gap analysis across baseline levels

## Run Tests

```bash
cd backend
pytest tests/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODE` | `mock` or `groq` | `mock` |
| `GROQ_API_KEY` | Groq API key | - |
| `DATABASE_URL` | SQLite path | `sqlite:///./data/copilot.db` |
| `SANDBOX_TIMEOUT` | Code execution timeout (s) | `2` |

## License

MIT License - For research and educational purposes.
