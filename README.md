# Autonomous Demand Forecasting System for Retail Businesses Using Deep Learning

An enterprise-ready, modular retail optimization platform built with Flask, TensorFlow/Keras, and Prophet. This application processes historical sales data, trains deep learning models (LSTMs and GRUs) and seasonal forecast pipelines (Prophet) to predict future daily demands, calculates Economic Order Quantities (EOQ) and Safety Stock, generates operational reorder alerts, and exports detailed business reports.

---

## 🌟 Core Features

1. **Robust Authentication & 2FA**: Complete registration, login, logout, email verification, password recovery, and session management with a 2FA One-Time Password (OTP) verification stage.
2. **Interactive Analytics Dashboard**: Beautiful Bootstrap 5 layouts rendering Monthly Revenue, Predicted demand volumes, low stock warnings, sales trends, top-selling lines, and category shares utilizing Chart.js.
3. **Product Catalog CRUD**: Categorized product inventory tracking with auto-initialized inventory optimization variables.
4. **Historical Sales Ingestion**: Clean CSV/Excel transaction history parser with column validation, format converters, and transactional import logs.
5. **Deep Learning Engine**: Time-series preprocessing using sliding windows and MinMax scalers. Automatically trains, evaluates (MAE, RMSE, MAPE, $R^2$), and deploys the best forecasting models.
6. **Inventory Optimization**: Computes mathematical Safety Stock, Reorder Points (ROP), and Economic Order Quantities (EOQ) to minimize holding costs and prevent stockouts.
7. **Proactive Alert Center**: Color-coded notifications for stockouts, low-stock triggers, forecast anomalies, and overstock warning metrics.
8. **Reports Exporter**: Generates CSV data sheets, Excel sheets, and ReportLab PDF documents with stylized tables, layout metrics, and alternating row colors.
9. **User Management & Audit Trail**: Admin tools to manage roles and delete user accounts, alongside database audit trails log tables.

---

## 🛠️ Technology Stack

- **Backend Framework**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-JWT-Extended
- **AI / Deep Learning**: TensorFlow, Keras (LSTM & GRU), Facebook Prophet, Scikit-learn
- **Data Engineering**: Pandas, NumPy, OpenPyXL
- **Visualization**: Chart.js (via frontend CDN)
- **Reporting**: ReportLab (PDF), python-csv, pandas (Excel)
- **Deployment**: Docker, Docker Compose, Nginx, Gunicorn

---

## 🚀 Setup & Running Instructions

### Method 1: Local Installation (Python)

1. **Clone or navigate to the workspace**:
   ```bash
   cd "c:\Users\ganes\Documents\demand forecasting"
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Seed the database**:
   This initializes tables, creates default users, and generates 365 days of mock sales history (with weekly seasonality and winter peaks) to make the models trainable immediately:
   ```bash
   python scripts/seed.py
   ```
   *Pre-seeded users:*
   - **Admin**: `admin@demandforecast.com` / Password: `AdminPass123!`
   - **Manager**: `manager@demandforecast.com` / Password: `ManagerPass123!`
   - **Staff**: `staff@demandforecast.com` / Password: `StaffPass123!`

5. **Run the application**:
   ```bash
   python run.py
   ```
   Open `http://127.0.0.1:5000` in your web browser. Check the terminal console to copy the mock OTP verification codes generated during login.

---

### Method 2: Containerized Deployment (Docker)

Ensure you have Docker and Docker Compose installed, then execute:

1. **Build and start services**:
   ```bash
   docker-compose up --build
   ```

2. **Access the application**:
   Open `http://localhost` (Nginx proxies all traffic from port 80 to Gunicorn on port 5000).

3. **Initialize the database inside the container** (Optional, if tables are blank):
   ```bash
   docker exec -it demand_forecasting_web python scripts/seed.py
   ```

---

### Method 3: Mobile Application wrapper (Capacitor)

The mobile application acts as a standalone PWA shell bridging the web view.

1. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

2. **Initialize Capacitor Android Platform**:
   ```bash
   npx cap add android
   ```

3. **Build / Sync assets**:
   ```bash
   npx cap sync
   ```

4. **Run in Android Emulator / Device**:
   Open the project inside Android Studio and build the APK or run directly using:
   ```bash
   npx cap open android
   ```
   *Note: For local emulator debugging, `capacitor.config.json` points to `http://10.0.2.2:5000` which routes directly to the Flask server running on the host system. Update `server.url` to your production domain before building release packages.*

---

## 🧪 Verification & Testing

Verify code structure, mathematical formulas, and route authorization using the automated test suite:

- **Run all tests**:
  ```bash
  python -m pytest
  ```
- **Test Authentication & 2FA**:
  ```bash
  python -m pytest tests/test_auth.py
  ```
- **Test AI Forecasting Preprocessor**:
  ```bash
  python -m pytest tests/test_ai_engine.py
  ```
- **Test Inventory Calculations (EOQ, ROP)**:
  ```bash
  python -m pytest tests/test_inventory.py
  ```

---

## 📂 Project Structure

```
├── app/
│   ├── blueprints/       # Route controllers (auth, products, sales, AI, inventory, etc.)
│   ├── models/           # SQLAlchemy DB Models (User, Product, Sale, Inventory, Alerts, etc.)
│   ├── services/         # Core business logic (AIEngine, InventoryOps, ReportService)
│   ├── static/           # CSS design systems (light/dark variables) and JS actions
│   └── templates/        # Jinja2 HTML pages (login, dashboard, catalog, alerts, reports)
├── scripts/              # Database seeder scripts (seed.py)
├── tests/                # Pytest verification suite
├── Dockerfile            # Image builder instructions
├── docker-compose.yml    # Service orchestration
├── nginx.conf            # Reverse proxy configuration
├── requirements.txt      # Python dependencies manifest
└── run.py                # WSGI entry point
```
