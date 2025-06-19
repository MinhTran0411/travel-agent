# Trip Enrichment Service

A FastAPI-based service that enriches trip plans with additional metadata such as images, reviews, and pricing information.

## Features

- Enriches trip activities with images, reviews, and pricing information
- MongoDB integration for storing enriched data
- Modular design for future microservice architecture
- Caching of activity metadata to reduce redundant enrichment

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=trip_enrichment
```

4. Run the service:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py           # Configuration settings
├── models/             # Pydantic models
├── schemas/            # Database schemas
├── services/           # Business logic
│   ├── enrichment.py   # Activity enrichment service
│   └── scraping.py     # Web scraping utilities
└── repositories/       # Database repositories
``` 