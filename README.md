# Travel Agent Monorepo

This monorepo contains all the components for the Travel Agent application:

## Components

1. **Mobile App** (`/mobile-app`)
   - React Native application
   - Handles user interface and interactions
   - Communicates with backend API

2. **Backend** (`/backend`)
   - Spring Boot application
   - RESTful API endpoints
   - MongoDB integration
   - OAuth2 security with Keycloak

3. **Auth Server** (`/auth-server`)
   - Keycloak authentication server
   - PostgreSQL database
   - Docker Compose setup
   - Initial realm configuration

4. **Orchestrator** (`/orchestrator`)
   - Python service with LangChain
   - Local and cloud LLM integration
   - Trip planning orchestration

## Prerequisites

- Docker and Docker Compose
- Java 17 or later
- Node.js 18 or later
- Python 3.9 or later
- MongoDB
- PostgreSQL

## Getting Started

1. Start the authentication server:
```bash
cd auth-server
docker-compose up -d
```

2. Start the backend service:
```bash
cd backend
./mvnw spring-boot:run
```

3. Start the orchestrator service:
```bash
cd orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

4. Start the mobile app:
```bash
cd mobile-app
npm install
npm run android  # or npm run ios
```

## Development

Each component has its own README with specific development instructions. Please refer to the individual component directories for more details. 