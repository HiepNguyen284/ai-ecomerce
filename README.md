# ShopVerse - Nen tang thuong mai dien tu Microservices

ShopVerse la du an e-commerce full-stack duoc tach thanh nhieu microservice va chay bang Docker Compose.

## 1. Tong quan kien truc

- Gateway: Caddy reverse proxy, dinh tuyen toan bo request vao frontend va cac API service
- Frontend: React + Vite
- Backend: 5 Django services
    - user-service
    - product-service
    - cart-service
    - order-service
    - payment-service
- Database: PostgreSQL 17 dung chung 1 instance, tach database theo service

## 2. Cong va dia chi truy cap

| Thanh phan | Truy cap tu may host |
|---|---|
| Frontend + API Gateway | http://localhost:8080 |
| Gateway healthcheck | http://localhost:8080/health |
| PostgreSQL (host port) | localhost:5444 |

Ghi chu:
- Cac service noi bo trong Docker network van ket noi DB qua ecommerce-db:5432
- Frontend goi API qua duong dan /api (cung origin voi gateway)

## 3. Quick start

### 3.1 Yeu cau

- Docker Desktop (hoac Docker Engine + Compose plugin)

### 3.2 Chay du an

```bash
docker compose up -d --build
```

Sau khi chay xong:
- Mo trinh duyet: http://localhost:8080
- Kiem tra trang thai container:

```bash
docker compose ps
```

### 3.3 Dung du an

```bash
docker compose down
```

Neu muon xoa toan bo du lieu DB (volume):

```bash
docker compose down -v
```

## 4. Seed du lieu san pham

product-service tu dong goi lenh seed khi container khoi dong.

Ban hien tai:
- 12 category
- Mac dinh 240 san pham (20 san pham/category)
- Gia duoc scale theo thi truong Viet Nam (VND)
- Moi san pham co image_url rieng

Danh sach category:
- Smartphones
- Laptops
- Audio
- Clothing
- Shoes
- Home Appliances
- Kitchen
- Books
- Gaming
- Watches
- Sports & Fitness
- Beauty & Care

### 4.1 Reseed thu cong

Seed 240 san pham (mac dinh):

```bash
docker exec ecommerce-product-service python manage.py seed_products --per-category 20 --seed 2026
```

Seed 300 san pham:

```bash
docker exec ecommerce-product-service python manage.py seed_products --per-category 25 --seed 2026
```

Luu y:
- Lenh seed la kieu upsert theo slug, co the chay lai de cap nhat du lieu ma khong tao trung lap khong kiem soat.

## 5. API route qua gateway

Tat ca API deu di qua gateway tai http://localhost:8080.

- /api/users/* -> user-service
- /api/products/* -> product-service
- /api/cart/* -> cart-service
- /api/orders/* -> order-service
- /api/payments/* -> payment-service

## 6. Endpoint chinh theo service

### User Service (/api/users/)
- POST /register/
- POST /login/
- GET /profile/
- POST /validate-token/ (internal)

### Product Service (/api/products/)
- GET /
- GET /<slug>/
- GET /categories/
- POST /stock-check/ (internal)

### Cart Service (/api/cart/)
- GET /
- POST /add/
- PUT /items/<id>/
- DELETE /items/<id>/

### Order Service (/api/orders/)
- GET /
- POST /create/
- GET /<id>/
- POST /<id>/cancel/

### Payment Service (/api/payments/)
- POST /create/
- GET /
- GET /order/<id>/

## 7. Xac thuc

He thong dung JWT. Gui token qua header:

```http
Authorization: Bearer <token>
```

## 8. Ket noi PostgreSQL tu may host

Thong so mac dinh:
- Host: localhost
- Port: 5444
- User: postgres
- Password: postgres

Vi du dung psql:

```bash
psql -h localhost -p 5444 -U postgres -d product_db
```

## 9. Cau truc thu muc chinh

```text
ai-ecomerce/
├── docker-compose.yml
├── gateway/
│   └── Caddyfile
├── frontend/
│   ├── src/
│   └── Dockerfile
├── services/
│   ├── user-service/
│   ├── product-service/
│   ├── cart-service/
│   ├── order-service/
│   └── payment-service/
└── database/
        └── init.sql
```

## 10. Troubleshooting nhanh

1. Frontend khong hien thi du lieu
- Kiem tra gateway va frontend dang chay:

```bash
docker compose ps
```

- Kiem tra health gateway:

```bash
curl http://localhost:8080/health
```

2. DB khong ket noi duoc tu host
- Kiem tra map cong 5444:5432 trong docker-compose.yml
- Kiem tra container ecommerce-db dang healthy

3. Muon xem log realtime

```bash
docker compose logs -f gateway frontend product-service
```
