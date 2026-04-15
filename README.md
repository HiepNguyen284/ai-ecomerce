# 🛒 ShopVerse — Microservice E-Commerce Platform

A full-stack e-commerce platform built with a **microservice architecture**, powered by Docker.

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Caddy Gateway (:80)                │
│              (Reverse Proxy + Load Balancer)          │
└──────┬────────┬────────┬────────┬────────┬───────────┘
       │        │        │        │        │
  ┌────▼──┐ ┌──▼────┐ ┌─▼───┐ ┌─▼────┐ ┌─▼──────┐
  │ User  │ │Product│ │Cart │ │Order │ │Payment │
  │Service│ │Service│ │Svc  │ │Svc   │ │Service │
  └───┬───┘ └──┬────┘ └──┬──┘ └──┬───┘ └───┬────┘
      │        │         │       │          │
  ┌───▼───┐ ┌──▼────┐ ┌──▼──┐ ┌─▼────┐ ┌──▼─────┐
  │UserDB │ │ProdDB │ │CartDB│ │OrdDB │ │PayDB   │
  │PG 17  │ │PG 17  │ │PG 17│ │PG 17 │ │PG 17   │
  └───────┘ └───────┘ └─────┘ └──────┘ └────────┘
```

## 🚀 Tech Stack

| Component       | Technology        |
|-----------------|-------------------|
| **Frontend**    | React 18 + Vite   |
| **Backend**     | Django 5.1 + DRF  |
| **Database**    | PostgreSQL 17     |
| **API Gateway** | Caddy 2           |
| **Container**   | Docker + Compose  |

## 📁 Project Structure

```
ai-ecomerce/
├── docker-compose.yml          # Orchestration
├── gateway/
│   └── Caddyfile               # API Gateway config
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/         # Navbar, Footer
│   │   ├── pages/              # Home, Products, Cart, Orders, Auth
│   │   └── services/           # API client
│   └── Dockerfile
└── services/
    ├── user-service/            # Authentication & Users
    ├── product-service/         # Product catalog (13 seeded products)
    ├── cart-service/            # Shopping cart
    ├── order-service/           # Order management
    └── payment-service/         # Payment processing
```

## 🏃 Quick Start

```bash
# Clone and run
docker-compose up --build

# Access the app
open http://localhost:8080
```

## 📡 API Endpoints

### User Service (`/api/users/`)
- `POST /register/` — Register new user
- `POST /login/` — Login + JWT token
- `GET /profile/` — Get user profile
- `POST /validate-token/` — Validate JWT (internal)

### Product Service (`/api/products/`)
- `GET /` — List all products (search, filter, sort)
- `GET /<slug>/` — Product detail
- `GET /categories/` — List categories
- `POST /stock-check/` — Check stock (internal)

### Cart Service (`/api/cart/`)
- `GET /` — Get user cart
- `POST /add/` — Add item to cart
- `PUT /items/<id>/` — Update quantity
- `DELETE /items/<id>/` — Remove item

### Order Service (`/api/orders/`)
- `GET /` — List user orders
- `POST /create/` — Create order from cart
- `GET /<id>/` — Order detail
- `POST /<id>/cancel/` — Cancel order

### Payment Service (`/api/payments/`)
- `POST /create/` — Process payment
- `GET /` — List user payments
- `GET /order/<id>/` — Payment by order

## 🔒 Authentication

JWT-based authentication. Include token in requests:
```
Authorization: Bearer <token>
```

## 🌱 Seed Data

Product service auto-seeds **13 products** across 4 categories on first boot:
- Electronics (4 products)
- Clothing (3 products)
- Home & Kitchen (3 products)
- Books (2 products)
