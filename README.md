# 🧬 Sentinel - AI-Driven AMR Surveillance Platform

### 🎓 A Final-Year Research Project | Sri Lanka Institute of Information Technology (SLIIT)  
**Collaborating Institution:** Teaching Hospital Peradeniya  
**Supervisors:**  
- Dr. Dinuka Wijendra – Senior Lecturer, SLIIT  
- Dr. Wasana Kudagammana – Consultant Microbiologist, Teaching Hospital Peradeniya  

---

## 📖 Overview  
**Sentinel** is an AI-powered surveillance system for predicting **antibiotic resistance patterns** and detecting **ward-level infection outbreaks** in hospital settings. By analyzing retrospective microbiology data, the system provides **early, data-driven insights** to support clinicians in **selecting effective antibiotics** and **preventing hospital-acquired infections**.

The platform focuses on four major pathogen groups commonly responsible for healthcare-associated infections, integrating machine learning and data analytics to enhance infection control decision-making.

---

## 🔬 Core Surveillance Modules  

### 1. **MRSA Prediction (Staphylococci)**  
Predicts methicillin resistance in *Staphylococcus aureus* using early-stage metadata such as sample type, ward, and patient demographics—enabling clinicians to identify MRSA infections before full lab confirmation.  

### 2. **STP Surveillance (Streptococcus & Enterococcus)**  
Monitors time-series infection trends to identify sudden ward-level clusters, providing early warnings to infection control units to initiate preventive measures.  

### 3. **ESBL Risk Scoring (Enterobacterales)**  
Assesses the likelihood of *E. coli* and *Klebsiella* isolates being ESBL-producing based on patient history, hospital stay duration, and preliminary lab results—guiding early antibiotic escalation decisions.  

### 4. **Non-Fermenter Surveillance (Pseudomonas & Acinetobacter)**  
Tracks resistance anomalies across wards, detecting unusual spikes and environmental contamination risks through continuous data surveillance.  

---

## 🧠 Methodology  

- **Data Source:** Retrospective microbiology and patient data from Teaching Hospital Peradeniya  
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
- Enables **faster clinical decision-making** in antibiotic prescription  
- Assists **infection control units** in identifying early outbreak signals  
- Promotes **rational antibiotic use** and supports national antimicrobial stewardship goals  
- Demonstrates how AI can enhance **public health preparedness** using existing hospital data  

---

## ⚙️ Technical Stack  
| Component | Technologies |
|-----------|--------------|
| **Frontend** | React, Vite, TailwindCSS, Recharts |
| **Backend** | FastAPI, Python |
| **Database** | PostgreSQL, Supabase |
| **AI/ML** | scikit-learn, XGBoost, LightGBM, TensorFlow |
| **Deployment** | Docker, Docker Compose |
| **Version Control** | Git, GitHub |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB RAM minimum
- Windows/Linux/Mac

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YohanPasi/ai-antibiotic-surveillance.git
   cd ai-antibiotic-surveillance
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs

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

> Dissanayake, S.H.J.A., Hettige, M.H.T.P., Jayalath, K.N.R., & Nishshanke, K.T.Y.P.  
> *Sentinel: AI-Driven Prediction and Surveillance of Antibiotic Resistance and Ward-Level Outbreaks.*  
> Sri Lanka Institute of Information Technology (SLIIT), Faculty of Computing, 2026.

---

## 🧩 Future Work  
- Integration with hospital electronic medical records (EMR)  
- Real-time deployment as a web-based infection control dashboard  
- Expansion to include fungal and viral resistance modules  
- Mobile application for ward-level notifications  

---

## 📄 License  
This project is part of academic research conducted at SLIIT in collaboration with Teaching Hospital Peradeniya.

---

**Version**: 2.0.0  
**Last Updated**: January 2026  
**Project Status**: Active Development
