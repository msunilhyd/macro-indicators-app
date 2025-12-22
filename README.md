# Macro Indicators Dashboard

A full-stack web application for visualizing macroeconomic indicators and historical data, similar to [indiamacroindicators.co.in](https://indiamacroindicators.co.in/).

## Tech Stack

- **Frontend**: Next.js 14, React, TailwindCSS, Recharts
- **Backend**: FastAPI (Python), SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)

## Project Structure

```
macro-indicators-app/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── database.py       # Database configuration
│   │   ├── config.py         # App settings
│   │   └── routers/          # API routes
│   │       ├── categories.py
│   │       ├── indicators.py
│   │       └── dashboard.py
│   ├── seed_data.py          # Script to load CSV data
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router pages
│   │   ├── components/       # React components
│   │   └── lib/              # API utilities
│   ├── package.json
│   └── next.config.js
└── README.md
```

## Quick Start

### 1. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database with CSV data
python seed_data.py

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the frontend dev server
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/categories` | List all categories |
| `GET /api/categories/{slug}` | Get category with indicators |
| `GET /api/indicators` | List all indicators |
| `GET /api/indicators/{slug}` | Get indicator with data points |
| `GET /api/indicators/{slug}/latest` | Get latest value |
| `GET /api/dashboard` | Get key dashboard indicators |
| `GET /api/dashboard/summary` | Get summary statistics |

## Data Source

The data comes from the `macrotrends_data_v2` folder containing:
- **Market Indexes**: S&P 500, Dow Jones, NASDAQ, international indexes
- **Precious Metals**: Gold, Silver, Platinum prices
- **Energy**: Oil, Natural Gas prices
- **Commodities**: Agricultural and industrial commodities
- **Exchange Rates**: Currency exchange rates
- **Interest Rates**: Fed rates, Treasury yields
- **Economy**: Unemployment, Inflation, GDP, etc.

## Features

- 📊 Dashboard with key economic indicators
- 📈 Interactive charts with historical data
- 🔍 Browse indicators by category
- 📱 Responsive design (mobile-friendly)
- ⚡ Fast data loading with SQLite/PostgreSQL

## Production Deployment

For production, update the `.env` file with a PostgreSQL connection:

```
DATABASE_URL=postgresql://user:password@host:5432/macro_indicators
```

## License

MIT License - For educational purposes only.
# macro-indicators-app
# macro-indicators-app
# macro-indicators-app
