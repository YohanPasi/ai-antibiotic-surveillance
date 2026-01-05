
# 🧬 AI-Driven Prediction and Surveillance of Antibiotic Resistance and Ward-Level Outbreaks  

### 🎓 A Final-Year Research Project | Sri Lanka Institute of Information Technology (SLIIT)  
**Collaborating Institution:** Teaching Hospital Peradeniya  
**Supervisors:**  
- Dr. Dinuka Wijendra – Senior Lecturer, SLIIT  
- Dr. Wasana Kudagammana – Consultant Microbiologist, Teaching Hospital Peradeniya  

---

## 📖 Overview  
This research project aims to develop an **AI-powered surveillance system** capable of predicting **antibiotic resistance patterns** and detecting **ward-level infection outbreaks** in hospital settings.  
By analyzing retrospective microbiology data, the system provides **early, data-driven insights** to support clinicians in **selecting effective antibiotics** and **preventing hospital-acquired infection clusters**.

The project focuses on four major pathogen groups commonly responsible for healthcare-associated infections in Sri Lanka, integrating machine learning and data analytics to enhance infection control decision-making.

---

## 🔬 Core Functionalities  

### 1. **MRSA Prediction (Staphylococci Module)**  
Predicts methicillin resistance in *Staphylococcus aureus* using early-stage metadata such as sample type, ward, and patient demographics—enabling clinicians to identify MRSA infections before full lab confirmation.  

### 2. **Outbreak Detection (Streptococcus Module)**  
Monitors time-series infection trends to identify sudden ward-level clusters of *Streptococcus* infections, providing early warnings to infection control units to initiate preventive measures.  

### 3. **ESBL Risk Scoring (Enterobacterales Module)**  
Assesses the likelihood of *E. coli* and *Klebsiella* isolates being ESBL-producing based on patient history, hospital stay duration, and preliminary lab results—guiding early antibiotic escalation decisions.  

### 4. **Resistance Trend Monitoring (Non-Fermenter Module)**  
Tracks resistance anomalies in *Pseudomonas* and *Acinetobacter* across wards, detecting unusual spikes and environmental contamination risks through continuous data surveillance.  

---

## 🧠 Methodology  

- **Data Source:** Retrospective microbiology and patient data from Teaching Hospital Peradeniya.  
- **Data Inputs:**  
  - Sample type, ward, age, sex, and diagnosis  
  - Organism identified and antibiotic susceptibility patterns  
  - Hospital stay duration and prior antibiotic exposure  
- **Machine Learning Models:**  
  - Gradient Boosting, Neural Networks, and Change-Point Detection algorithms  
- **Model Outputs:**  
  - Probability of resistance per isolate  
  - Outbreak alerts per ward  
  - Risk scores visualized in real-time dashboards  

---

## 🏥 Research Impact  
- Enables **faster clinical decision-making** in antibiotic prescription.  
- Assists **infection control units** in identifying early outbreak signals.  
- Promotes **rational antibiotic use** and supports national antimicrobial stewardship goals.  
- Demonstrates how AI can enhance **public health preparedness** using existing hospital data.  

---

## ⚙️ Technical Stack  
| Component | Technologies |
|------------|--------------|
| **Data Processing** | Python (pandas, NumPy), SQL |
| **Modeling & AI** | scikit-learn, LightGBM, TensorFlow |
| **Visualization** | Power BI, Streamlit |
| **Version Control** | Git, GitHub |
| **Documentation** | Markdown, LaTeX (report generation) |

---

## 📊 Dataset and Ethics  
All data used in this study are **anonymized** and handled under strict **ethical and confidentiality guidelines** approved by the **Teaching Hospital Peradeniya** Ethics Committee.  
The dataset consists of one year of microbiology culture data, including blood, urine, respiratory, and wound isolates with corresponding antibiotic sensitivity profiles.

---

## 👩‍💻 Research Team  
| Name | Role | Specialization |
|------|------|----------------|
| **S.H.J.A. Dissanayake** | Team Lead | MRSA Prediction & Model Integration |
| **M.H.T.P. Hettige** | Researcher | ESBL Risk Scoring & Data Processing |
| **K.N.R. Jayalath** | Researcher | Streptococcus Outbreak Detection |
| **K.T.Y.P. Nishshanke** | Researcher | Non-Fermenter Trend Analysis |

---

## 🧾 Citation  
If you use this work in your research, please cite as:  

> Dissanayake, S.H.J.A., Hettige, M.H.T.P., Jayalath, K.N.R., & Nishshanke, K.T.Y.P..  
> *AI-Driven Prediction and Surveillance of Antibiotic Resistance and Ward-Level Outbreaks.*  
> Sri Lanka Institute of Information Technology (SLIIT), Faculty of Computing.

---

## 🧩 Future Work  
- Integration with hospital electronic medical records (EMR).  
- Real-time deployment as a web-based infection control dashboard.  
- Expansion to include fungal and viral resistance modules.  

---


=======
# AST Prediction System

AI-Driven Antibiotic Susceptibility Testing Prediction & Surveillance for Non-Fermenting Bacteria

## 🎯 Project Overview

This system predicts next week's Antibiotic Susceptibility Percentage (S%) for non-fermenting bacteria (*Pseudomonas aeruginosa* and *Acinetobacter spp.*) at the ward level, providing early warning alerts via a traffic-light system to support antimicrobial stewardship.

### Key Features

- **Multi-Model Ensemble**: SMA, Facebook Prophet, and ARIMA with rolling-origin cross-validation
- **Ward-Level Predictions**: Granular predictions when data sufficient (≥10 records)  
- **Traffic-Light Alerts**: Intuitive 🟢 Green / 🟡 Amber / 🔴 Red system
- **Transparent AI**: Always displays model used, MAE score, and confidence intervals
- **Docker-Based**: Complete containertized architecture for easy deployment

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│   FastAPI Backend│────▶│   PostgreSQL DB │
│  (Port 3000)    │     │    (Port 8000)   │     │   (Port 5432)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
      Vite + Tailwind      Prophet + ARIMA          Weekly Aggregated
      Recharts Charts      Model Training           AST Data & Models
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 4GB RAM minimum
- Windows/Linux/Mac

### Installation

1. **Clone or navigate to project directory**:
   ```bash
   cd d:\Yohan\Project
   ```

2. **Place your dataset**:
   - Ensure `Raw/Version_1_9_Final_Clean_NoMissing.xlsx` is in place

3. **Start all services**:
   ```bash
   docker-compose up --build
   ```

4. **Wait for services** to be healthy (~2-3 minutes):
   - Database: Initializing schema and permissions
   - API: Installing Python dependencies
   - Frontend: Installing Node packages

5. **Load data** (in new terminal):
```bash
# Clean and load raw data
docker-compose exec api python /app/data_processor/clean_and_load.py

# Aggregate to weekly S%
docker-compose exec api python /app/data_processor/aggregate_weekly.py
```

6. **Train models** (coming in Step 3):
   ```bash
   docker-compose exec api python /app/models/model_trainer.py
   ```

7. **Access the application**:
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Database: `localhost:5432` (user: ast_user, db: ast_db)

## 📊 Data Pipeline

### 1. Data Cleaning (`clean_and_load.py`)

- **S/I/R Standardization**: "s", "S  ", "sensitive" → "S"
- **Organism Mapping**:
  - "Non-fermenter" / "NLF" → *Pseudomonas aeruginosa*
  - Acinetobacter variants → standardized naming
- **Conflict Resolution**: Multiple S/I/R values → Intermediate (I)

### 2. Weekly Aggregation (`aggregate_weekly.py`)

- **S% Calculation**: `S% = (S count) / (S + I + R count) × 100`
- **Continuous Time Series**: Missing weeks filled with NaN
- **Data Sufficiency**: Flags combinations with ≥10 records

### 3. Model Training

- **Rolling-Origin Cross-Validation**: Train on weeks 1-N, predict N+1
- **MAE Selection**: Best model (lowest MAE) chosen automatically
- **Three Models**:
  - Simple Moving Average (baseline)
  - Facebook Prophet (uncertainty intervals)
  - ARIMA (statistical forecasting)

## 🎨 Traffic-Light System

| Color | S% Threshold | Meaning |
|-------|--------------|---------|
| 🟢 Green | ≥ 80% | Good susceptibility - low resistance risk |
| 🟡 Amber | 60-79% | Moderate concern - monitor closely |
| 🔴 Red | < 60% | High resistance risk - immediate action |

## 📁 Project Structure

```
d:/Yohan/Project/
├── api/                           # FastAPI Backend
│   ├── data_processor/            # Data ETL scripts
│   │   ├── clean_and_load.py     # Excel → PostgreSQL
│   │   └── aggregate_weekly.py   # Weekly S% aggregation
│   ├── models/                    # ML model implementations
│   │   ├── base_model.py         # Abstract base class
│   │   ├── sma_model.py          # Simple Moving Average
│   │   ├── prophet_model.py      # Facebook Prophet
│   │   ├── arima_model.py        # ARIMA/SARIMA
│   │   └── model_trainer.py      # Training orchestration
│   ├── main.py                    # FastAPI application
│   ├── database.py                # DB connection management
│   ├── schemas.py                 # Pydantic models
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # API container config
├── frontend/                      # React Application
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── App.jsx                # Main app component
│   │   └── index.css              # TailwindCSS styles
│   ├── package.json               # Node dependencies
│   ├── vite.config.js             # Vite configuration
│   ├── tailwind.config.js         # Tailwind theme
│   └── Dockerfile                 # Frontend container config
├── database/                      # PostgreSQL Setup
│   ├── schema.sql                 # Database schema
│   └── init.sql                   # Initialization script
├── Raw/                           # Input Data
│   └── Version_1_9_Final_Clean_NoMissing.xlsx
├── docker-compose.yml             # Service orchestration
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `ast_user` | Database username |
| `POSTGRES_PASSWORD` | `ast_password_2024` | Database password |
| `POSTGRES_DB` | `ast_db` | Database name |
| `DATABASE_URL` | Auto-configured | Full DB connection string |

### Model Parameters

Edit model files in `api/models/` to adjust:
- SMA window size (default: 4 weeks)
- Prophet changepoint sensitivity
- ARIMA order parameters

## 🧪 Testing

### Health Checks

```bash
# Check all services
docker-compose ps

# Test database connection
docker-compose exec db psql -U ast_user -d ast_db -c "SELECT version();"

# Test API health
curl http://localhost:8000/health
```

### Data Verification

```bash
# Check raw data count
docker-compose exec db psql -U ast_user -d ast_db -c "SELECT COUNT(*) FROM ast_raw_data;"

# Check weekly aggregation
docker-compose exec db psql -U ast_user -d ast_db -c "SELECT organism, COUNT(*) FROM ast_weekly_aggregated GROUP BY organism;"

# View sufficient data records
docker-compose exec db psql -U ast_user -d ast_db -c "SELECT COUNT(*) FROM ast_weekly_aggregated WHERE has_sufficient_data = TRUE;"
```

## 📖 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status |
| `/health` | GET | Health check |
| `/api/options` | GET | Available wards/organisms/antibiotics |
| `/api/historical` | GET | Historical S% time series |
| `/api/predict` | POST | Generate next week prediction |
| `/api/model-performance` | GET | Model MAE comparison |

Full API documentation: http://localhost:8000/api/docs

## 🛠️ Development

### Local Development (without Docker)

**Backend**:
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

**Database**:
- Set up local PostgreSQL 16
- Run `database/schema.sql`

### Hot Reload

Docker Compose is configured for hot reload:
- **Frontend**: Changes reflect immediately (Vite HMR)
- **Backend**: Auto-reloads on file changes (uvicorn --reload)

## 📝 Current Implementation Status

✅ **Step 1 Complete**: Environment & Database Setup
- Docker Compose orchestration
- PostgreSQL schema with all tables
- FastAPI backend structure
- React frontend with dark theme

✅ **Step 2 Complete**: Data Processing Pipeline
- Data cleaning with organism mapping
- Weekly aggregation with S% calculation
- Database ingestion scripts

🚧 **Step 3 In Progress**: Model Training
- Base model framework
- SMA, Prophet, ARIMA implementations
- Rolling-origin cross-validation

⏳ **Step 4 Pending**: API Endpoints
⏳ **Step 5 Pending**: Frontend Components
⏳ **Step 6 Pending**: Testing & Verification

## 🔒 Security Notes

- Default credentials in `docker-compose.yml` are for **development only**
- Change passwords before production deployment
- Database is exposed on `localhost:5432` for development
- Production should use Docker networks (not exposed ports)

## 📚 References

- [Facebook Prophet Documentation](https://facebook.github.io/prophet/)
- [Statsmodels ARIMA Guide](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## 👥 Support

For issues or questions:
1. Check logs: `docker-compose logs [service-name]`
2. Review API docs: http://localhost:8000/api/docs
3. Verify data: Use SQL queries in Testing section

## 📄 License

Internal project for antimicrobial stewardship surveillance.

---

**Version**: 1.0.0  
**Last Updated**: 2025-12-30
>>>>>>> Yohan
