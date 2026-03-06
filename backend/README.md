# UrbanPulse Backend — Spring Boot 3 + MySQL

REST API and WebSocket server for the UrbanPulse smart city platform.

## Prerequisites

- Java 21+
- Maven 3.9+
- MySQL 8.0+

## Database Setup (MySQL)

```sql
CREATE DATABASE urbanpulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'urbanpulse_user'@'localhost' IDENTIFIED BY 'urbanpulse_pass';
GRANT ALL PRIVILEGES ON urbanpulse.* TO 'urbanpulse_user'@'localhost';
FLUSH PRIVILEGES;
```

## Run

```bash
mvn spring-boot:run
# API available at http://localhost:8080/api
```

## Key Endpoints

| Method | Endpoint               | Auth        | Description                 |
| ------ | ---------------------- | ----------- | --------------------------- |
| POST   | /auth/register         | Public      | Register new user           |
| POST   | /auth/login            | Public      | Login, returns JWT          |
| GET    | /incidents             | Public      | List incidents (filterable) |
| POST   | /incidents             | JWT         | Submit new incident         |
| PATCH  | /incidents/{id}/status | STAFF/ADMIN | Update incident status      |
| GET    | /agent-logs            | STAFF/ADMIN | AI agent decision log       |
| GET    | /dashboard/stats       | STAFF/ADMIN | KPI summary                 |

## Default Test Users (password: test123 for all)

- admin@urbanpulse.com (ADMIN)
- staff@urbanpulse.com (STAFF)
- ahmet@example.com (CITIZEN)

## WebSocket

Connect to `ws://localhost:8080/api/ws` (SockJS/STOMP)

- Subscribe `/topic/incidents/new` — new incident events
- Subscribe `/topic/incidents/update` — status change events
- Subscribe `/topic/agents/activity` — agent pipeline notifications
