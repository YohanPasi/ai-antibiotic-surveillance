# Sentinel AMR Surveillance Platform

## Project Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sentinel Platform Architecture                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  React Frontend │────────▶│  FastAPI Backend│────────▶│   PostgreSQL    │
│   (Port 3000)   │         │   (Port 8000)   │         │   (Supabase)    │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                            │                            │
        │                            │                            │
        ▼                            ▼                            ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  Vite + Tailwind│         │  ML Models      │         │  Raw AST Data   │
│  Recharts       │         │  XGBoost/LSTM   │         │  Aggregated     │
│  React Router   │         │  Prophet/ARIMA  │         │  Model Storage  │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

## Module Architecture

### MRSA Prediction Module
```
Patient Data → Feature Engineering → XGBoost Model → Risk Score → Alert System
     │              │                     │              │            │
     └─────────────▶│                     │              │            │
                    └────────────────────▶│              │            │
                                          └─────────────▶│            │
                                                         └───────────▶│
```

### STP Surveillance Module
```
Weekly AST Data → Time Series Analysis → LSTM/Prophet → Trend Prediction → Ward Alerts
      │                  │                    │               │              │
      └─────────────────▶│                    │               │              │
                         └───────────────────▶│               │              │
                                              └──────────────▶│              │
                                                               └─────────────▶│
```

### ESBL Risk Engine
```
Lab Results → Risk Assessment → Two-Stage Model → Clinical Recommendation
    │              │                  │                    │
    └─────────────▶│                  │                    │
                   └─────────────────▶│                    │
                                      └───────────────────▶│
```

### Non-Fermenter Surveillance
```
Culture Data → Ward Aggregation → Trend Analysis → Outbreak Detection
     │              │                   │                 │
     └─────────────▶│                   │                 │
                    └──────────────────▶│                 │
                                        └────────────────▶│
```

---

## Technology Stack Details

### Frontend Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI Framework |
| Vite | 5.0.11 | Build Tool & Dev Server |
| TailwindCSS | 3.4.1 | Styling Framework |
| React Router | 6.21.3 | Client-side Routing |
| Recharts | 2.10.3 | Data Visualization |
| Lucide React | 0.562.0 | Icon Library |
| Framer Motion | 12.23.26 | Animations |
| Axios | 1.6.5 | HTTP Client |

### Backend Technologies
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API Framework |
| Python 3.10+ | Core Language |
| Uvicorn | ASGI Server |
| Pydantic | Data Validation |
| SQLAlchemy | ORM |

### Machine Learning
| Library | Purpose |
|---------|---------|
| scikit-learn | Core ML Algorithms |
| XGBoost | Gradient Boosting |
| LightGBM | Efficient Boosting |
| TensorFlow | Deep Learning |
| Prophet | Time Series Forecasting |
| statsmodels | Statistical Models |

### Database & Storage
| Technology | Purpose |
|------------|---------|
| PostgreSQL 16 | Primary Database |
| Supabase | Hosted PostgreSQL |
| Docker Volumes | Persistent Storage |

---

## Directory Structure

```
ai-antibiotic-surveillance/
├── frontend/                 # React Application
│   ├── src/
│   │   ├── components/       # Reusable UI Components
│   │   │   ├── esbl/        # ESBL Module Components
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   └── MainLayout.jsx
│   │   ├── context/         # React Context (Auth, Theme)
│   │   ├── pages/           # Page Components
│   │   │   └── stp/         # STP Module Pages
│   │   ├── services/        # API Services
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── api/                      # FastAPI Backend
│   ├── models/              # ML Model Implementations
│   │   ├── mrsa_artifacts/  # MRSA Model Files
│   │   ├── base_model.py
│   │   ├── sma_model.py
│   │   ├── prophet_model.py
│   │   └── arima_model.py
│   ├── data_processor/      # Data ETL Scripts
│   ├── main.py             # FastAPI Application
│   ├── database.py         # DB Connection
│   ├── schemas.py          # Pydantic Models
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/
│   ├── schema.sql          # Database Schema
│   └── init.sql            # Initialization
│
├── Models/                  # Trained Models
│   ├── esbl_xgb_early_v1_metadata.json
│   └── esbl_xgb_v1_metadata.json
│
├── Config/                  # Configuration Files
│   ├── antibiotic_outcome_tables.json
│   ├── esbl_early_thresholds.json
│   ├── esbl_model_config.json
│   └── governance_rules.json
│
├── Raw/                     # Input Data
│   └── Version_1_9_Final_Clean_NoMissing.xlsx
│
├── docker-compose.yml
├── README.md
├── CHANGELOG.md
├── INSTALLATION.md
└── ARCHITECTURE.md         # This File
```

---

## Data Flow

### 1. Data Ingestion
```
Excel Files → Python Processor → PostgreSQL → API Endpoints → React UI
```

### 2. Prediction Pipeline
```
User Input → API Request → Feature Engineering → ML Model → Prediction → Response
```

### 3. Surveillance Pipeline
```
Scheduled Job → Data Aggregation → Pattern Detection → Alert Generation → UI Notification
```

---

## Security Architecture

### Authentication Flow
```
1. User Login → 2. JWT Token → 3. Protected Routes → 4. Role-Based Access
```

### Data Security
- Encrypted database connections (SSL/TLS)
- HTTPS for all API communications
- JWT-based stateless authentication
- Role-based access control (RBAC)
- Anonymized patient data
- Audit logging for all predictions

---

## Deployment Architecture

### Development
```
Docker Compose → Local Containers → Hot Reload → Development Server
```

### Production
```
Git Repository → CI/CD Pipeline → Docker Build → Container Registry → Production Server
```

---

## Performance Considerations

### Frontend Optimization
- Code splitting with React.lazy()
- Image optimization
- Vite build optimization
- CDN for static assets

### Backend Optimization
- Connection pooling
- Caching frequently accessed data
- Async request handling
- Model prediction caching

### Database Optimization
- Indexed columns for queries
- Materialized views for aggregations
- Query optimization
- Regular vacuum and analyze

---

## Scalability

### Horizontal Scaling
- Stateless API design
- Load balancer ready
- Database replication support
- Microservices architecture potential

### Vertical Scaling
- Configurable resource limits
- Optimized model inference
- Efficient data processing
- Memory management

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Maintained By**: SLIIT Research Team
