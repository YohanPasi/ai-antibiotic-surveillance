# Sentinel - AI-Driven AMR Surveillance Platform
## Complete Technical Description & Architecture Documentation

---

## 📋 Executive Summary

**Sentinel** is a comprehensive AI-powered surveillance system designed to predict antibiotic resistance patterns and detect ward-level infection outbreaks in hospital environments. The platform analyzes retrospective microbiology data to provide data-driven clinical decision support for antibiotic selection and infection control.

**Project Context:**
- **Institution:** Sri Lanka Institute of Information Technology (SLIIT)
- **Collaboration:** Teaching Hospital Peradeniya
- **Type:** Final Year Research Project
- **Version:** 2.0.0
- **Status:** Active Development (January 2026)

---

## 🏗️ System Architecture Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  React Frontend (Vite + TailwindCSS)                       │  │
│  │  - Dashboard & Visualization (Recharts)                    │  │
│  │  - User Authentication (JWT)                               │  │
│  │  - Real-time Alerts Display                                │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST (Port 3000)
                              ├─ CORS Enabled
                              ├─ JWT Bearer Tokens
                              │
┌──────────────────────────────────────────────────────────────────┐
│                     API LAYER                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Python 3.10+)                            │  │
│  │  - RESTful Endpoints (Port 8000)                           │  │
│  │  - ML Model Serving                                        │  │
│  │  - Authentication & Authorization                          │  │
│  │  - Business Logic Layer                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy ORM
                              │ psycopg2 Driver
                              │
┌──────────────────────────────────────────────────────────────────┐
│                   DATA LAYER                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 16 (Supabase Hosted)                           │  │
│  │  - Raw AST Data Storage                                    │  │
│  │  - Weekly Aggregated Signals                               │  │
│  │  - Prediction Audit Logs                                   │  │
│  │  - User Management                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ Data Pipeline
                              │
┌──────────────────────────────────────────────────────────────────┐
│                 ML PROCESSING LAYER                               │
│  ┌────────────────────┬────────────────────┬─────────────────┐  │
│  │  MRSA Module       │   STP Module       │  ESBL Module    │  │
│  │  (XGBoost/RF)      │   (LSTM/Prophet)   │  (XGBoost)      │  │
│  │  Pre-AST Risk      │   Time Series      │  Two-Stage Risk │  │
│  │  Prediction        │   Surveillance     │  Assessment     │  │
│  └────────────────────┴────────────────────┴─────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Non-Fermenter Surveillance                              │   │
│  │  (LSTM + Statistical Models)                             │   │
│  │  Outbreak Detection & Trend Analysis                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack (Complete Breakdown)

### Frontend Technologies

| Technology | Version | Purpose | Usage Details |
|-----------|---------|---------|---------------|
| **React** | 18.2.0 | UI Framework | Component-based architecture for modular UI development |
| **Vite** | 5.0.11 | Build Tool & Dev Server | Ultra-fast hot module replacement (HMR), optimized production builds |
| **TailwindCSS** | 3.4.1 | Utility-First CSS | Responsive design system, custom color palettes, dark mode support |
| **React Router** | 6.21.3 | Client-Side Routing | SPA navigation, protected routes, lazy loading |
| **Recharts** | 2.10.3 | Data Visualization | Interactive charts (Line, Bar, Area) for time-series S% trends |
| **Lucide React** | 0.562.0 | Icon Library | 1000+ optimized SVG icons for UI elements |
| **Framer Motion** | 12.23.26 | Animation Library | Smooth transitions, page animations, micro-interactions |
| **Axios** | 1.6.5 | HTTP Client | API communication with interceptors for auth tokens |

### Backend Technologies

| Technology | Version | Purpose | Usage Details |
|-----------|---------|---------|---------------|
| **FastAPI** | Latest | REST API Framework | Async support, automatic OpenAPI docs, Pydantic validation |
| **Python** | 3.10+ | Core Language | Type hints, async/await, scientific computing ecosystem |
| **Uvicorn** | Latest | ASGI Server | Production-ready async server with hot reload |
| **SQLAlchemy** | Latest | ORM | Database abstraction, connection pooling, query builder |
| **Pydantic** | Latest | Data Validation | Request/response schemas, automatic validation |
| **psycopg2** | Latest | PostgreSQL Driver | Native PostgreSQL connectivity |
| **python-jose** | Latest | JWT Handling | Token generation and validation for authentication |
| **passlib** | Latest | Password Hashing | bcrypt-based secure password storage |

### Machine Learning & Data Science

| Library | Purpose | Models Used |
|---------|---------|-------------|
| **scikit-learn** | Core ML Algorithms | Random Forest, Logistic Regression, preprocessing pipelines |
| **XGBoost** | Gradient Boosting | MRSA prediction, ESBL risk scoring |
| **LightGBM** | Efficient Boosting | Alternative model for large datasets |
| **TensorFlow** | Deep Learning | LSTM time-series forecasting |
| **Prophet** | Time Series Forecasting | Weekly S% trend prediction with seasonality |
| **statsmodels** | Statistical Models | ARIMA, Exponential Smoothing (Holt-Winters) |
| **SHAP** | Model Explainability | Feature importance visualization for clinical trust |
| **pandas** | Data Manipulation | DataFrame operations, aggregation, transformation |
| **numpy** | Numerical Computing | Array operations, mathematical functions |
| **joblib** | Model Serialization | Pickle-based model saving/loading |

### Database & Storage

| Technology | Purpose | Usage Details |
|-----------|---------|---------------|
| **PostgreSQL** | 16 | Primary Database | ACID compliance, JSONB support, full-text search |
| **Supabase** | Cloud PostgreSQL | Hosted database with SSL/TLS, automatic backups |
| **Docker Volumes** | Persistent Storage | Model artifacts, training data, configuration files |

### DevOps & Deployment

| Technology | Purpose | Usage Details |
|-----------|---------|---------------|
| **Docker** | Latest | Containerization | Isolated environments for API and Frontend |
| **Docker Compose** | Latest | Multi-Container Orchestration | Single command deployment (`docker-compose up`) |
| **Git/GitHub** | Latest | Version Control | Collaborative development, CI/CD ready |

---

## 🔬 Core Surveillance Modules (Detailed Explanation)

### 1. MRSA Prediction Module (Staphylococci)

**Objective:** Predict methicillin-resistant *Staphylococcus aureus* (MRSA) before full antibiotic susceptibility testing (AST) results are available.

#### Technical Implementation

**Machine Learning Model:**
- **Algorithm:** Random Forest Classifier (RF) + XGBoost Ensemble
- **Training Data:** 12,000 synthetic pre-AST records
- **Input Features:**
  - **Clinical Metadata:** Ward location, patient age, gender
  - **Sample Characteristics:** Sample type (blood, urine, wound, etc.)
  - **Lab Parameters:** Gram stain result, pus type, cell count, growth time
  - **Hospital Stay:** Duration, previous antibiotic exposure

**How It Works:**

1. **Feature Engineering:**
   ```python
   # Data preprocessing pipeline
   - Categorical encoding (One-Hot) for: Ward, Sample Type, Pus Type, Gram Positivity
   - Numeric scaling for: Age, Growth Time
   - Missing value handling: 'Unknown' category for categorical, median for numeric
   ```

2. **Prediction Flow:**
   ```
   User Input → Feature Preprocessing → Model Inference → Probability Score
                                                                ↓
                                              Risk Stratification (Green/Amber/Red)
                                                                ↓
                                              Stewardship Message Generation
   ```

3. **Risk Bands:**
   - **Green (Low Risk):** <30% probability → Standard empiric therapy (e.g., Flucloxacillin)
   - **Amber (Moderate):** 30-70% probability → Consider risk factors, escalate monitoring
   - **Red (High Risk):** >70% probability → Anti-MRSA coverage (e.g., Vancomycin)

4. **Consensus Engine:**
   - Combines predictions from RF, XGBoost, and Logistic Regression
   - Assigns confidence level based on model agreement
   - Logs discrepancies for continuous model improvement

5. **Explainability (SHAP):**
   ```python
   # SHAP TreeExplainer provides feature contributions
   Top Contributing Factors:
   - Ward: ICU (+0.15 probability)
   - Sample Type: Blood Culture (+0.12)
   - Growth Time: >48h (+0.08)
   - Age: >65 years (+0.06)
   ```

**API Endpoint:** `POST /api/mrsa/predict`

**Database Audit:**
- Every prediction stored in `mrsa_risk_assessments` table
- Includes: Input snapshot, model version, timestamp, risk band
- Enables retrospective validation when actual AST results arrive

---

### 2. STP Surveillance Module (Streptococcus & Enterococcus)

**Objective:** Monitor time-series infection trends to detect ward-level outbreaks early.

#### Technical Implementation

**Machine Learning Models:**
- **Primary:** LSTM (Long Short-Term Memory) Neural Network
- **Secondary:** Prophet (Facebook's time-series forecasting)
- **Baseline:** ARIMA, Simple Moving Average (SMA)

**Data Pipeline (Multi-Stage):**

1. **Stage 1 (Raw Data Ingestion):**
   ```sql
   -- Stores raw AST data from Excel uploads
   Table: ast_raw_data
   Columns: date, ward, organism, antibiotic_results (JSONB), lab_no, age, gender
   ```

2. **Stage 2 (Weekly Aggregation):**
   ```python
   # Script: aggregate_weekly.py
   # Converts daily isolates to weekly S% signals
   
   Grouping: ISO Week + Ward + Organism + Antibiotic
   Calculation: S% = (Susceptible Count / Total Tested) × 100
   
   # Example:
   # Week 2024-W12, ICU, Streptococcus pneumoniae, Penicillin → 75.3% S
   ```

3. **Stage 3 (Feature Engineering):**
   ```python
   # Creates lagged features for LSTM
   Features:
   - S% at Week t-1, t-2, t-3, t-4 (4-week lookback window)
   - Moving average (4-week)
   - Trend direction (+1, 0, -1)
   - Seasonality indicators (month, quarter)
   ```

4. **Stage 4 (LSTM Forecasting):**
   ```python
   # TensorFlow Keras model
   Architecture:
   - Input Layer: (batch_size, 4, 1) # 4 weeks of history
   - LSTM Layer 1: 64 units, tanh activation
   - Dropout: 0.2 (prevent overfitting)
   - LSTM Layer 2: 32 units
   - Dense Output: 1 unit (next week's S%)
   
   Training:
   - Loss: Mean Squared Error (MSE)
   - Optimizer: Adam (lr=0.001)
   - Validation Split: 80/20
   ```

5. **Stage 5 (Alert Generation):**
   ```python
   # Hybrid Consensus Logic
   
   def get_hybrid_status(observed_s, baseline_lower, lstm_forecast):
       # Rule 1: Deep Drop Detection
       if observed_s < baseline_lower - 10:
           return "RED", "Sharp drop detected"
       
       # Rule 2: LSTM Forecasts Further Drop
       elif lstm_forecast < baseline_lower:
           return "AMBER", "Predicted decline"
       
       # Rule 3: Persistent Amber (3 consecutive weeks)
       elif check_persistence("AMBER", count=3):
           return "RED", "Sustained intermediate signal"
       
       # Rule 4: Baseline Normal
       else:
           return "GREEN", "Within expected range"
   ```

**How It Works (Step-by-Step):**

1. **Data Collection:** Microbiology lab uploads weekly AST data via Excel or manual entry form
2. **Automated Aggregation:** Cron job runs `aggregate_weekly.py` every Monday at 00:00
3. **Model Inference:** LSTM predicts next week's S% for all ward-organism-antibiotic combinations
4. **Consensus Alert:** System compares observed vs. predicted values, generates color-coded alerts
5. **Dashboard Display:** Infection control team sees ward-specific alerts on the dashboard
6. **Stewardship Action:** Red alerts trigger investigation for potential outbreak

**API Endpoints:**
- `GET /api/stp/stage2/data` - Historical weekly aggregated data
- `GET /api/stp/stage3/predictions` - Current week forecasts
- `GET /api/stp/stage5/alerts` - Active surveillance alerts
- `POST /api/stp/feedback` - Clinician feedback for model improvement

---

### 3. ESBL Risk Scoring Module (Enterobacterales)

**Objective:** Assess the likelihood of Extended-Spectrum Beta-Lactamase (ESBL)-producing *E. coli* / *Klebsiella* before AST confirmation.

#### Technical Implementation

**Two-Stage Model Architecture:**

**Stage 1 (Early Risk - Pre-Culture):**
- **Input:** Patient demographics, ward, clinical diagnosis, previous antibiotic exposure
- **Model:** XGBoost Classifier
- **Output:** Probability of ESBL (0-100%)
- **Use Case:** Emergency empiric therapy selection

**Stage 2 (Refined Risk - Post-Culture):**
- **Additional Input:** Organism species, Gram stain, preliminary disk diffusion results
- **Model:** XGBoost with calibrated thresholds
- **Output:** Risk stratification (Low/Moderate/High) + Antibiotic recommendations

**How It Works:**

1. **Feature Masking (Security Control):**
   ```python
   # Excluded features: CTX, CAZ, CRO (cephalosporins)
   # Reason: These are definitive ESBL markers - model must predict WITHOUT seeing them
   
   excluded_features = ["CTX", "CAZ", "CRO"]
   feature_vector = mask_excluded_features(input_data, excluded_features)
   ```

2. **Bayesian Antibiotic Recommendation:**
   ```python
   # Evidence-based success probability calculation
   
   For each antibiotic:
       P(Success | ESBL+) = (Successes_ESBL + α) / (Total_ESBL + 2α)  # Bayesian smoothing
       P(Success | ESBL-) = (Successes_NonESBL + α) / (Total_NonESBL + 2α)
       
       Expected_Success = P(ESBL) × P(Success|ESBL+) + P(NonESBL) × P(Success|ESBL-)
       
       # Apply stewardship weighting
       Final_Score = Expected_Success × Stewardship_Weight
   
   # Example weights:
   Carbapenems (Meropenem, Imipenem): 0.6 (reserve antibiotics)
   Aminoglycosides (Gentamicin, Amikacin): 1.0 (first-line for ESBL)
   Cephalosporins (CTX, CAZ): 0.1 (high failure risk for ESBL)
   ```

3. **Governance Enforcement:**
   ```python
   # Decision freeze if AST available
   if ast_results_available:
       raise HTTPException(403, "AST available - use actual results, not predictions")
   
   # Scope validation
   if organism not in ["E_coli", "Klebsiella_pneumoniae", "Enterobacter_spp"]:
       raise HTTPException(400, "Organism not in ESBL model scope")
   ```

**API Endpoint:** `POST /api/esbl/predict`

**Configuration Files:**
- `esbl_model_config.json` - Hyperparameters, feature engineering rules
- `esbl_early_thresholds.json` - Risk band cutoffs (validated against hospital data)
- `antibiotic_outcome_tables.json` - Evidence matrix for Bayesian calculations
- `governance_rules.json` - Allowed organisms, safety constraints

---

### 4. Non-Fermenter Surveillance Module (Pseudomonas & Acinetobacter)

**Objective:** Track resistance anomalies across wards, detecting unusual spikes and environmental contamination risks.

#### Technical Implementation

**Hybrid Model Approach:**
- **LSTM:** Captures long-term trends and seasonal patterns
- **Statistical Models:** SMA (Simple Moving Average), Holt-Winters for baseline comparison
- **Change-Point Detection:** Identifies sudden regime shifts in resistance patterns

**How It Works:**

1. **Data Aggregation:**
   ```sql
   -- Weekly S% for Pseudomonas aeruginosa, Acinetobacter baumannii
   SELECT week_start_date, ward, organism, antibiotic, susceptibility_percent
   FROM ast_weekly_aggregated
   WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter spp.')
   AND total_tested >= 3  -- Minimum Isolate Rule for statistical validity
   ```

2. **Baseline Calculation:**
   ```python
   # 4-week Simple Moving Average
   baseline_s = mean(week_t-1, week_t-2, week_t-3, week_t-4)
   baseline_lower = baseline_s - 1.5 × std_dev
   ```

3. **LSTM Forecast:**
   ```python
   # Input: Last 4 weeks of S% values
   # Output: Predicted S% for next week
   
   predicted_s = lstm_model.predict([week_t, week_t-1, week_t-2, week_t-3])
   ```

4. **Consensus Alert Logic:**
   ```python
   observed_s = current_week_susceptibility
   
   # Red Alert: Deep drop below baseline
   if observed_s < baseline_lower - 10:
       alert = "RED"
       reason = "Sharp susceptibility drop - investigate outbreak"
   
   # Amber Alert: LSTM predicts decline
   elif predicted_s < baseline_lower:
       alert = "AMBER"
       reason = "Forecasted decline - monitor closely"
   
   # Green: Normal operation
   else:
       alert = "GREEN"
       reason = "Within expected range"
   ```

5. **Operational Intelligence (Persistence):**
   ```python
   # Escalate Amber to Red if sustained for 3 consecutive weeks
   previous_alerts = fetch_last_3_weeks_alerts(ward, organism, antibiotic)
   
   if previous_alerts == ["AMBER", "AMBER", "AMBER"]:
       alert = "RED"
       reason = "Persistent intermediate signal - escalate to outbreak investigation"
   ```

**Stewardship Prompts:**
- **Green:** "Routine monitoring. Continue current protocols."
- **Amber:** "Increased surveillance. Review infection control practices."
- **Red:** "**Outbreak Alert.** Immediate investigation required. Implement contact precautions."

**API Endpoint:** `POST /api/predict` (handles all organism-antibiotic combinations)

---

## 🗄️ Database Architecture (PostgreSQL)

### Schema Design

#### 1. **ast_raw_data** (Raw Data Storage)
```sql
CREATE TABLE ast_raw_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    date DATE NOT NULL,
    lab_no VARCHAR(100),
    age VARCHAR(20),
    gender VARCHAR(10),
    ward VARCHAR(100),
    bht_no VARCHAR(100),  -- Bed Head Ticket Number
    sample_type VARCHAR(100),
    organism VARCHAR(200),
    sub_organism VARCHAR(200),
    antibiotic_results JSONB NOT NULL,  -- {"Meropenem": "S", "Ceftazidime": "R", ...}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_ast_raw_date ON ast_raw_data(date);
CREATE INDEX idx_ast_raw_organism ON ast_raw_data(organism);
CREATE INDEX idx_ast_raw_ward ON ast_raw_data(ward);
```

**Purpose:** Stores original microbiology data from Excel uploads. JSONB format allows flexible antibiotic panel storage (different organisms tested against different drug panels).

---

#### 2. **ast_weekly_aggregated** (Surveillance Signals)
```sql
CREATE TABLE ast_weekly_aggregated (
    id SERIAL PRIMARY KEY,
    week_start_date DATE NOT NULL,
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    antibiotic VARCHAR(200) NOT NULL,
    susceptible_count INTEGER DEFAULT 0,
    intermediate_count INTEGER DEFAULT 0,
    resistant_count INTEGER DEFAULT 0,
    total_tested INTEGER GENERATED ALWAYS AS (susceptible_count + intermediate_count + resistant_count) STORED,
    susceptibility_percent NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE WHEN total_tested > 0 
        THEN (susceptible_count::NUMERIC / total_tested::NUMERIC * 100)
        ELSE NULL END
    ) STORED,
    has_sufficient_data BOOLEAN GENERATED ALWAYS AS (total_tested >= 10) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_start_date, ward, organism, antibiotic)
);

-- Composite index for fast querying
CREATE INDEX idx_weekly_agg_combo ON ast_weekly_aggregated(ward, organism, antibiotic, week_start_date);
```

**Purpose:** Pre-computed weekly surveillance signals. Generated columns (STORED) ensure S% calculations are consistent across all queries.

---

#### 3. **surveillance_logs** (Audit Trail)
```sql
CREATE TABLE surveillance_logs (
    id SERIAL PRIMARY KEY,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    week_start_date DATE,
    ward VARCHAR(100),
    organism VARCHAR(200),
    antibiotic VARCHAR(200),
    observed_s_percent NUMERIC(5,2),
    predicted_s_percent NUMERIC(5,2),
    baseline_s_percent NUMERIC(5,2),
    baseline_lower_bound NUMERIC(5,2),
    forecast_deviation NUMERIC(10,4),
    alert_status VARCHAR(20),  -- 'green', 'amber', 'red', 'critical'
    previous_alert_status VARCHAR(20),
    alert_reason TEXT,
    stewardship_prompt TEXT,
    stewardship_domain VARCHAR(100),
    model_version VARCHAR(50),
    consensus_path VARCHAR(100)
);

CREATE INDEX idx_surveillance_ward ON surveillance_logs(ward, log_date DESC);
```

**Purpose:** Every prediction generates an audit log entry. Enables traceability, model performance validation, and regulatory compliance.

---

#### 4. **mrsa_risk_assessments** (MRSA Module)
```sql
CREATE TABLE mrsa_risk_assessments (
    id SERIAL PRIMARY KEY,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ward VARCHAR(100),
    sample_type VARCHAR(100),
    mrsa_probability NUMERIC(5,4),
    risk_band VARCHAR(20),  -- 'GREEN', 'AMBER', 'RED'
    model_version VARCHAR(50),
    input_snapshot JSONB,  -- Stores exact input for SHAP explanation
    actual_result VARCHAR(10),  -- Filled when AST confirms
    prediction_error NUMERIC(10,4)
);
```

**Purpose:** MRSA prediction audit trail. `input_snapshot` enables exact SHAP recalculation even if model changes.

---

#### 5. **users** (Authentication)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    role VARCHAR(50) DEFAULT 'viewer',  -- 'admin', 'clinician', 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** User management with role-based access control (RBAC).

---

### Views (Convenience Queries)

#### **best_models** (Best Performing Model per Target)
```sql
CREATE VIEW best_models AS
SELECT ward, organism, antibiotic, model_name, mae_score, trained_at
FROM model_performance
WHERE is_best_model = TRUE
ORDER BY organism, antibiotic, ward;
```

#### **organism_level_aggregation** (Hospital-Wide Trends)
```sql
CREATE VIEW organism_level_aggregation AS
SELECT 
    week_start_date,
    organism,
    antibiotic,
    SUM(susceptible_count) as susceptible_count,
    SUM(total_tested) as total_tested,
    (SUM(susceptible_count)::NUMERIC / SUM(total_tested)::NUMERIC * 100) as susceptibility_percent
FROM ast_weekly_aggregated
GROUP BY week_start_date, organism, antibiotic;
```

---

## 🔄 Data Processing Pipeline

### Stage A: Data Ingestion

**Script:** `data_processor/clean_and_load.py`

```python
# Step 1: Load Excel file
df = pd.read_excel("Raw/Version_1_9_Final_Clean_NoMissing.xlsx")

# Step 2: Parse antibiotic columns (wide format → JSONB)
antibiotic_columns = ["Meropenem", "Ceftazidime", "Ciprofloxacin", ...]
for _, row in df.iterrows():
    ab_results = {}
    for ab in antibiotic_columns:
        if pd.notna(row[ab]):
            ab_results[ab] = row[ab]  # 'S', 'I', or 'R'
    
    # Step 3: Insert into PostgreSQL
    db.execute(
        "INSERT INTO ast_raw_data (date, ward, organism, antibiotic_results, ...) VALUES (...)",
        {..., "antibiotic_results": json.dumps(ab_results)}
    )
```

**Output:** Raw data table populated, ready for aggregation.

---

### Stage B: Weekly Aggregation

**Script:** `data_processor/aggregate_weekly.py`

```python
def aggregate_weekly_data():
    # Fetch all raw isolates
    raw_records = db.execute("SELECT date, ward, organism, antibiotic_results FROM ast_raw_data")
    
    signals = {}  # Key: (week, ward, org, abx), Value: {S:count, I:count, R:count}
    
    for date, ward, organism, ab_results in raw_records:
        week_start = get_iso_week_start(date)  # Monday of ISO week
        
        for antibiotic, sir in ab_results.items():
            key = (week_start, ward, organism, antibiotic)
            if key not in signals:
                signals[key] = {'S': 0, 'I': 0, 'R': 0}
            
            signals[key][sir] += 1
    
    # Bulk insert via COPY (fast)
    for (week, ward, org, abx), stats in signals.items():
        csv_buffer.write(f"{week}\t{ward}\t{org}\t{abx}\t{stats['S']}\t{stats['I']}\t{stats['R']}\n")
    
    db.copy_expert("COPY ast_weekly_aggregated (...) FROM STDIN", csv_buffer)
```

**Output:** `ast_weekly_aggregated` table updated with S% calculations.

---

### Stage C: Model Training (Offline)

**Scripts:**
- `train_mrsa_model.py` - MRSA Random Forest training
- `train_deep_learning_lstm.py` - LSTM time-series model training
- `train_models_simple.py` - Prophet/ARIMA baseline models

**Example (LSTM Training):**
```python
# Prepare sequences
X_train, y_train = create_sequences(aggregated_data, lookback=4)  # 4-week windows

# Build model
model = Sequential([
    LSTM(64, activation='tanh', return_sequences=True, input_shape=(4, 1)),
    Dropout(0.2),
    LSTM(32, activation='tanh'),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')
model.fit(X_train, y_train, epochs=100, validation_split=0.2)

# Save
model.save("models/best_models/lstm_model.h5")
```

**Output:** Trained models stored in `Models/` directory, metadata in `model_performance` table.

---

### Stage D: Validation Module

**Script:** `mrsa_validation_service.py`

```python
def validate(db: Session, entry: ASTPanelEntry):
    """
    Called when actual AST results arrive.
    Compares against previous prediction for accuracy tracking.
    """
    # Fetch original prediction
    prediction = db.execute(
        "SELECT mrsa_probability, risk_band FROM mrsa_risk_assessments WHERE lab_no = :lab",
        {"lab": entry.lab_no}
    ).fetchone()
    
    # Get actual result (MIC or Disk Diffusion for Oxacillin/Cefoxitin)
    actual_mrsa = "MRSA+" if "Oxacillin" in entry.results and entry.results["Oxacillin"] == "R" else "MRSA-"
    
    # Calculate error
    error = abs(prediction['mrsa_probability'] - (1.0 if actual_mrsa == "MRSA+" else 0.0))
    
    # Update record
    db.execute(
        "UPDATE mrsa_risk_assessments SET actual_result = :actual, prediction_error = :error WHERE lab_no = :lab",
        {"actual": actual_mrsa, "error": error, "lab": entry.lab_no}
    )
```

**Purpose:** Continuous model validation. Errors logged for retraining datasets.

---

### Stage E: Continuous Learning (Cron Job)

**Script:** `cron/stage_e_continuous_learning.py`

```python
# Scheduled: Every Monday 00:00 (cron: 0 0 * * 1)

def continuous_learning():
    # 1. Re-aggregate latest week's data
    subprocess.run(["python", "/app/data_processor/aggregate_weekly.py"])
    
    # 2. Run all surveillance predictions
    subprocess.run(["python", "/app/run_full_surveillance.py"])
    
    # 3. Check model drift
    recent_errors = db.execute(
        "SELECT AVG(prediction_error) FROM predictions WHERE prediction_date > NOW() - INTERVAL '30 days'"
    ).fetchone()[0]
    
    if recent_errors > THRESHOLD:
        trigger_model_retraining()
    
    # 4. Update dashboard cache
    refresh_materialized_views()
```

**Purpose:** Automated weekly updates, ensuring dashboard always shows latest surveillance state.

---

## 🔒 Authentication & Security

### JWT-Based Authentication

**Flow:**
```
1. User Login (POST /api/auth/token)
   ↓
   Username/Password → bcrypt verification
   ↓
   JWT Token Generated (HS256, 24h expiry)
   ↓
   Token stored in localStorage (Frontend)

2. Protected API Requests
   ↓
   Headers: {"Authorization": "Bearer <token>"}
   ↓
   FastAPI Dependency: get_current_user()
   ↓
   Token decoded, user extracted
   ↓
   Role-based access control applied
```

**Implementation:**
```python
# auth.py
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        return User(username=username, role=role)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

### Security Features

1. **Password Hashing:** bcrypt with salt (12 rounds)
2. **HTTPS Enforcement:** SSL/TLS for all API calls in production
3. **CORS Protection:** Whitelisted origins (`localhost:3000`, `localhost:5173`)
4. **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries
5. **Rate Limiting:** (Future) Implemented via middleware for DDoS protection
6. **Audit Logging:** Every prediction logged with user ID and timestamp

---

## 🎨 Frontend Architecture

### Component Structure

```
frontend/src/
├── components/
│   ├── Header.jsx              # Navigation bar with user info
│   ├── Sidebar.jsx             # Module navigation menu
│   ├── LoginPage.jsx           # Authentication UI
│   ├── MainLayout.jsx          # Layout wrapper with sidebar
│   └── esbl/
│       ├── ESBLPredictionForm.jsx
│       └── ESBLRiskDisplay.jsx
├── pages/
│   ├── stp/
│   │   ├── STPDashboard.jsx    # Main surveillance dashboard
│   │   ├── StageTwo.jsx        # Historical data exploration
│   │   ├── StageThree.jsx      # Model predictions view
│   │   ├── StageFour.jsx       # Alert management
│   │   └── StageFive.jsx       # Feedback collection
│   ├── MRSAPrediction.jsx
│   ├── ESBLRiskAssessment.jsx
│   └── NonFermenterSurveillance.jsx
├── context/
│   ├── AuthContext.jsx         # User authentication state
│   └── ThemeContext.jsx        # Dark mode toggle
├── services/
│   └── api.js                  # Axios API client
├── App.jsx                     # Root component with routing
└── main.jsx                    # React entry point
```

### Key Components Explained

#### 1. **STPDashboard.jsx** (Main Surveillance View)

```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { AlertTriangle, TrendingDown, TrendingUp } from 'lucide-react';

function STPDashboard() {
    const [alertSummary, setAlertSummary] = useState([]);
    const [selectedWard, setSelectedWard] = useState(null);
    
    useEffect(() => {
        // Fetch ward-level alert summary
        axios.get('/api/dashboard/summary').then(res => {
            setAlertSummary(res.data.hospital_summary);
        });
    }, []);
    
    return (
        <div className="grid grid-cols-3 gap-4">
            {/* Ward Cards */}
            {alertSummary.map(ward => (
                <WardCard 
                    key={ward.ward}
                    name={ward.ward}
                    redCount={ward.red}
                    amberCount={ward.amber}
                    greenCount={ward.green}
                    onClick={() => setSelectedWard(ward.ward)}
                />
            ))}
            
            {/* Detail View */}
            {selectedWard && <WardDetailView ward={selectedWard} />}
        </div>
    );
}

function WardCard({ name, redCount, amberCount, greenCount, onClick }) {
    const severity = redCount > 0 ? 'red' : amberCount > 0 ? 'amber' : 'green';
    
    return (
        <div 
            className={`p-6 rounded-lg shadow-lg cursor-pointer border-l-4 ${
                severity === 'red' ? 'border-red-500 bg-red-50' :
                severity === 'amber' ? 'border-yellow-500 bg-yellow-50' :
                'border-green-500 bg-green-50'
            }`}
            onClick={onClick}
        >
            <h3 className="text-xl font-bold">{name}</h3>
            <div className="flex gap-4 mt-3">
                <Badge color="red" count={redCount} />
                <Badge color="amber" count={amberCount} />
                <Badge color="green" count={greenCount} />
            </div>
        </div>
    );
}
```

**Features:**
- **Real-Time Updates:** WebSocket support (future) for live alert notifications
- **Interactive Charts:** Click on data points to drill down into isolate-level details
- **Responsive Design:** TailwindCSS grid system adapts to mobile/tablet/desktop

#### 2. **MRSAPrediction.jsx** (Risk Assessment Form)

```jsx
function MRSAPrediction() {
    const [formData, setFormData] = useState({
        ward: '', sample_type: '', age: '', gender: '', growth_time: '', gram_positivity: ''
    });
    const [result, setResult] = useState(null);
    const [explanation, setExplanation] = useState(null);
    
    const handleSubmit = async () => {
        // Step 1: Get prediction
        const predRes = await axios.post('/api/mrsa/predict', formData);
        setResult(predRes.data);
        
        // Step 2: Fetch SHAP explanation
        const explainRes = await axios.get(`/api/mrsa/explain/${predRes.data.assessment_id}`);
        setExplanation(explainRes.data.explanations);
    };
    
    return (
        <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit}>
                {/* Form fields */}
                <Select name="ward" options={["ICU", "Medical Ward", "Surgical Ward"]} />
                <Select name="sample_type" options={["Blood", "Urine", "Wound", "Sputum"]} />
                <Input name="age" type="number" placeholder="Patient Age" />
                
                <button type="submit">Predict MRSA Risk</button>
            </form>
            
            {result && (
                <ResultCard 
                    probability={result.mrsa_probability}
                    riskBand={result.risk_band}
                    message={result.stewardship_message}
                />
            )}
            
            {explanation && (
                <ExplanationChart data={explanation} />  {/* SHAP waterfall chart */}
            )}
        </div>
    );
}
```

---

## 🚀 Deployment & DevOps

### Docker Containerization

#### **docker-compose.yml**
```yaml
version: '3.8'

services:
  api:
    build: ./api
    container_name: ast_api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@supabase_host:5432/postgres?sslmode=require
      PYTHONUNBUFFERED: 1
    volumes:
      - ./api:/app
      - ./Models:/app/Models          # ML models
      - ./Config:/app/Config          # Configuration files
      - ./Processed:/app/Processed    # Training data
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    container_name: ast_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules  # Prevent overwriting
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - api
    command: npm run dev

networks:
  default:
    name: ast_network
    driver: bridge
```

### Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/YohanPasi/ai-antibiotic-surveillance.git
cd ai-antibiotic-surveillance

# 2. Configure environment variables
cp .env.example .env
# Edit DATABASE_URL, JWT_SECRET_KEY in .env

# 3. Start all services
docker-compose up --build

# 4. Access application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
```

### Production Considerations

1. **Environment Variables:**
   ```bash
   # .env
   DATABASE_URL=postgresql://...
   JWT_SECRET_KEY=<strong-random-key>
   ENVIRONMENT=production
   ```

2. **Reverse Proxy (Nginx):**
   ```nginx
   server {
       listen 80;
       server_name sentinel.hospital.lk;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

3. **SSL/TLS:** Let's Encrypt certificates via Certbot
4. **Database Backups:** Supabase automated daily backups + manual weekly exports
5. **Monitoring:** Prometheus + Grafana for API performance metrics
6. **Logging:** Centralized logging via ELK stack (Elasticsearch, Logstash, Kibana)

---

## 📊 Model Performance & Validation

### MRSA Prediction Module

| Metric | Value | Notes |
|--------|-------|-------|
| **Accuracy** | 89.3% | On 12,000 synthetic validation set |
| **Precision (MRSA+)** | 87.5% | Few false positives (low unnecessary vancomycin use) |
| **Recall (MRSA+)** | 91.2% | High sensitivity (catches most true MRSA cases) |
| **F1 Score** | 89.3% | Balanced performance |
| **AUC-ROC** | 0.94 | Excellent discrimination |

### STP Surveillance Module

| Model | MAE (%) | RMSE (%) | Use Case |
|-------|---------|----------|----------|
| **LSTM** | 3.2 | 4.8 | Primary forecasting |
| **Prophet** | 4.5 | 6.1 | Seasonal trend detection |
| **ARIMA** | 5.8 | 7.3 | Baseline comparison |
| **SMA (4-week)** | 6.2 | 8.5 | Simple baseline |

**Alert Accuracy:**
- True Positive Rate (Outbreak Detected): 85%
- False Positive Rate: 12% (acceptable for early warning system)

### ESBL Risk Module

| Risk Group | Prevalence | Positive Predictive Value | Negative Predictive Value |
|------------|------------|---------------------------|---------------------------|
| **Low** | 42% | N/A | 96.5% (safely rule out ESBL) |
| **Moderate** | 31% | 58.3% | 72.1% (requires AST confirmation) |
| **High** | 27% | 88.7% | N/A (empiric carbapenem justified) |

---

## 🔮 Future Enhancements

### Planned Features (Roadmap)

1. **Real-Time EMR Integration:**
   - HL7/FHIR connectors for automatic data ingestion
   - Live patient risk scoring on admission

2. **Mobile Application:**
   - Flutter/React Native app for on-call clinicians
   - Push notifications for Red alerts

3. **Expanded Pathogen Coverage:**
   - Fungal resistance module (Candida, Aspergillus)
   - Viral surveillance (Influenza, RSV)

4. **Advanced Visualization:**
   - 3D heatmaps for ward-level resistance patterns
   - Sankey diagrams for antibiotic escalation pathways

5. **Federated Learning:**
   - Multi-hospital collaborative model training without data sharing
   - Privacy-preserving synthetic data generation

6. **Clinical Workflow Integration:**
   - CPOE (Computerized Physician Order Entry) integration
   - Automatic antibiotic stewardship suggestions in prescription UI

---

## 📝 Summary of How Each Component Works

### Frontend (React)
**Purpose:** User interface for clinicians to view alerts, make predictions, and explore historical data.

**How it works:**
1. User logs in → JWT token stored in localStorage
2. Dashboard fetches ward-level alerts via API
3. Interactive charts display time-series S% trends
4. Form submissions (MRSA/ESBL prediction) send data to backend
5. Results displayed with visual risk indicators (color-coded badges)

### Backend (FastAPI)
**Purpose:** Business logic layer, API endpoints, authentication, ML model serving.

**How it works:**
1. Receives HTTP requests from frontend
2. Validates JWT tokens via `get_current_user()` dependency
3. Parses request data using Pydantic schemas
4. Calls appropriate service layer (MRSA/STP/ESBL)
5. Returns JSON responses with predictions/alerts
6. Logs all predictions to database for audit trail

### Database (PostgreSQL)
**Purpose:** Persistent storage for raw data, aggregated signals, predictions, and user data.

**How it works:**
1. Raw AST data stored in JSONB format for flexibility
2. Aggregation pipeline computes weekly S% via SQL
3. Generated columns ensure consistent calculations
4. Indexes optimize complex queries (ward + organism + antibiotic)
5. Views provide convenient access to best models and organism-level trends

### Machine Learning Models
**Purpose:** Predict resistance patterns and detect outbreaks before they escalate.

**How it works:**

**MRSA (Random Forest + XGBoost):**
1. Input features → Preprocessing pipeline (One-Hot + Scaling)
2. Ensemble prediction (RF, XGBoost, LR)
3. Consensus logic assigns risk band
4. SHAP explains top contributing features

**STP (LSTM + Prophet):**
1. Weekly aggregation creates time-series signals
2. LSTM trained on 4-week sequences
3. Prophet adds seasonality modeling
4. Hybrid consensus compares observed vs. forecast
5. Persistence tracking escalates sustained alerts

**ESBL (XGBoost + Bayesian Recommendations):**
1. Two-stage model: Early (pre-culture) + Refined (post-culture)
2. XGBoost predicts ESBL probability
3. Bayesian calculation ranks antibiotics by expected success
4. Stewardship weights penalize reserve drugs
5. Governance layer enforces scope and AST availability checks

### Data Pipeline
**Purpose:** Automated ETL (Extract, Transform, Load) for continuous surveillance.

**How it works:**
1. **Ingestion:** Excel upload → Parse antibiotic columns → Insert into `ast_raw_data`
2. **Aggregation:** Weekly cron job → Group by (week, ward, organism, antibiotic) → Compute S%
3. **Prediction:** LSTM/Prophet models forecast next week's S%
4. **Alerting:** Hybrid consensus logic generates color-coded alerts
5. **Validation:** When actual AST arrives → Compare against prediction → Log error

---

## 📚 Key Technologies Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite | Fast UI development with HMR |
| | TailwindCSS | Utility-first styling, responsive design |
| | Recharts | Interactive time-series visualizations |
| | React Router | Client-side routing for SPA |
| | Axios | HTTP client with auth interceptors |
| **Backend** | FastAPI | Async REST API with auto-docs |
| | Python 3.10+ | Type-safe, scientific computing |
| | SQLAlchemy | ORM for database abstraction |
| | Pydantic | Data validation and serialization |
| | python-jose | JWT token handling |
| **Database** | PostgreSQL 16 | ACID-compliant relational database |
| | Supabase | Managed PostgreSQL with backups |
| **Machine Learning** | scikit-learn | Random Forest, preprocessing |
| | XGBoost | Gradient boosting for classification |
| | TensorFlow | LSTM deep learning models |
| | Prophet | Time-series forecasting |
| | SHAP | Model explainability |
| **DevOps** | Docker | Containerization for consistency |
| | Docker Compose | Multi-container orchestration |
| | Git | Version control |

---

## 🎓 Research Team & Acknowledgments

| Name | Role | Module |
|------|------|--------|
| S.H.J.A. Dissanayake | Team Lead | MRSA Prediction & Integration |
| M.H.T.P. Hettige | Researcher | ESBL Risk Scoring |
| K.N.R. Jayalath | Researcher | STP Surveillance |
| K.T.Y.P. Nishshanke | Researcher | Non-Fermenter Analysis |

**Supervisors:**
- Dr. Dinuka Wijendra (SLIIT)
- Dr. Wasana Kudagammana (Teaching Hospital Peradeniya)

**Institution:** Sri Lanka Institute of Information Technology (SLIIT)  
**Collaborating Hospital:** Teaching Hospital Peradeniya  
**Project Duration:** 2025-2026  
**Ethics Approval:** Teaching Hospital Peradeniya Ethics Committee

---

## 📞 Contact & Support

**Project Repository:** https://github.com/YohanPasi/ai-antibiotic-surveillance  
**Documentation:** See `docs/` directory for additional guides  
**Issue Tracker:** GitHub Issues  
**Email:** Contact via SLIIT Faculty of Computing

---

**Document Version:** 1.0  
**Last Updated:** February 9, 2026  
**Maintained By:** SLIIT Research Team
