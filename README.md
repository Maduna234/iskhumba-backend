# Iskhumba Thash Electronix – Backend API

This is the production backend for the **Iskhumba Thash Electronix** business management platform. It provides a secure REST API for customer management, booking handling, payment tracking, gallery uploads, and user authentication.

---

## Table of Contents

- [Overview](#overview)
- [Technologies Used](#technologies-used)
- [Live API URL](#live-api-url)
- [Setup and Development](#setup-and-development)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
- [Deployment on Render](#deployment-on-render)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Admin Access Control](#admin-access-control)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [License](#license)

---

## Overview

The backend serves as the core engine for the Iskhumba Thash Electronix web application. It handles:

- User registration and authentication with JWT
- Role-based access control (admin / customer)
- Full CRUD operations for customers, bookings, and payments
- Image upload and management via Cloudinary
- Admin approval workflow for customer accounts
- Revenue tracking and booking status management

The API is built with Flask and uses PostgreSQL for data persistence with SQLAlchemy ORM.

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python 3.14** | Runtime environment |
| **Flask** | Web framework |
| **Flask-SQLAlchemy** | ORM for PostgreSQL |
| **Flask-JWT-Extended** | JWT authentication |
| **bcrypt** | Password hashing |
| **psycopg2-binary** | PostgreSQL adapter |
| **Cloudinary SDK** | Image upload and storage |
| **Gunicorn** | Production WSGI server |
| **python-dotenv** | Environment variable management |

---

## Live API URL

The backend is deployed and accessible at:

```
https://iskh**********.onrender.com
```

### Health Check Endpoint

To verify the API is running and database is connected:

```
https://iskh*********.onrender.com/api/test
```

---

## Setup and Development

### Prerequisites

- Python 3.12 or higher
- PostgreSQL (local or remote)
- Git
- Cloudinary account (for image uploads)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/Maduna234/iskhumba-backend.git
   cd iskhumba-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/iskhumba_db
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-here
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

5. Run the application:
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`.

---

## Deployment on Render

### PostgreSQL Database

1. Create a PostgreSQL database on [Render](https://render.com) (free tier).
2. Copy the **Internal Database URL** from the database dashboard.
3. This URL will be used as the `DATABASE_URL` environment variable.

### Web Service

1. Push your code to a GitHub repository.
2. On Render, create a new Web Service and connect your repository.
3. Configure the service:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or paid for better performance)
4. Add all environment variables listed below.
5. Deploy. Tables will be created automatically on first startup.

---

## Environment Variables

The following environment variables must be set for the application to work properly:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Flask session security key | `random-string-123` |
| `JWT_SECRET_KEY` | JWT encoding/decoding key | `random-string-456` |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | `hn*****` |
| `CLOUDINARY_API_KEY` | Cloudinary API key | `***********` |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | `FaD******` |

All variables are case-sensitive and must be set in the Render environment tab.

---

## API Endpoints

All endpoints are prefixed with `/api`. Authentication is required for protected routes using the JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Log in and receive JWT token | No |

### User Management (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | Get all users |
| PUT | `/users/<id>/approve` | Approve or reject a user |

### Customers

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/customers` | List all customers | Yes |
| POST | `/customers` | Create a new customer | Yes |
| PUT | `/customers/<id>` | Update a customer | Yes |
| DELETE | `/customers/<id>` | Delete a customer | Admin only |

### Bookings

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/bookings` | List bookings (admin: all, customer: own) | Yes |
| POST | `/bookings` | Create a new booking | Yes |
| PUT | `/bookings/<id>` | Update a booking | Yes |
| DELETE | `/bookings/<id>` | Delete a booking | Admin only |

### Payments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/payments` | List all payments | Yes |
| POST | `/payments` | Create a payment | Yes |
| PUT | `/payments/<id>` | Update a payment | Yes |
| DELETE | `/payments/<id>` | Delete a payment | Admin only |

### Gallery

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/gallery` | List all gallery images | Yes |
| POST | `/gallery/upload` | Upload one or more images | Admin only |
| DELETE | `/gallery/<id>` | Delete a gallery image | Admin only |

### Health Check

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/test` | Database connection test (returns customers) | No |

---

## Admin Access Control

Admin registration is restricted to specific email addresses for security.

### Allowed Admin Emails

Only the following emails can register as `admin`:

```
m*******@iskhumba.ac.za
s*******@iskhumba.ac.za
m*******@iskhumba.ac.za
```

### Registration Flow

- **Admin registration**: User selects `admin` role and email must be in the allowed list. Account is auto-approved.
- **Customer registration**: User selects `customer` role. Account requires admin approval before login.

### Approval Workflow

1. A customer registers with `role = customer` (auto-set `approved = False`).
2. An admin logs in and goes to the **Pending Users** tab in the dashboard.
3. The admin clicks **Approve** to activate the account.
4. The customer can now log in.

---

## Database Schema

### users

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `name` | VARCHAR(100) | Full name |
| `email` | VARCHAR(100) | Unique email |
| `password` | VARCHAR(255) | Hashed password |
| `role` | VARCHAR(20) | `admin` or `customer` |
| `approved` | BOOLEAN | Account approval status |
| `created_at` | TIMESTAMP | Registration date |

### customers

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `user_id` | INTEGER | References `users.id` |
| `name` | VARCHAR(100) | Full name |
| `phone` | VARCHAR(20) | Phone number |
| `email` | VARCHAR(100) | Email address |
| `address` | TEXT | Physical address |
| `created_at` | TIMESTAMP | Creation date |

### bookings

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `customer_id` | INTEGER | References `customers.id` |
| `package_name` | VARCHAR(100) | Package selected |
| `package_price` | VARCHAR(50) | Package price |
| `service_type` | VARCHAR(50) | `solar`, `cctv`, `gate`, `wiring` |
| `status` | VARCHAR(20) | `pending`, `confirmed`, `completed`, `cancelled` |
| `details` | TEXT | Additional notes |
| `created_at` | TIMESTAMP | Creation date |

### payments

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `booking_id` | INTEGER | References `bookings.id` |
| `amount` | DECIMAL(10,2) | Payment amount |
| `method` | VARCHAR(50) | `Cash`, `Bank Transfer`, `EFT`, `Card`, `Other` |
| `status` | VARCHAR(20) | `unpaid`, `paid`, `pending`, `partial` |
| `reference` | VARCHAR(100) | Payment reference |
| `created_at` | TIMESTAMP | Creation date |

### gallery

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `title` | VARCHAR(255) | Image title |
| `url` | VARCHAR(500) | Cloudinary URL |
| `created_at` | TIMESTAMP | Upload date |

---

## Project Structure

```
iskhumba-backend/
├── app.py              # Main application file (Flask routes, models)
├── config.py           # Configuration with environment variables
├── requirements.txt    # Python dependencies
├── runtime.txt         # Python version specification
├── .env                # Local environment variables (not committed)
├── uploads/            # Temporary upload folder (local development)
└── README.md           # This file
```

---

## License

This project is proprietary software owned by **Iskhumba Thash Electronix**.

All rights reserved. Unauthorized copying, distribution, or use of this software is strictly prohibited.

---

## Contact

For technical support or deployment assistance:

**Technical Lead**  
Mr. Maduna  
Email: simphiweyinkosimaduna@gmail.com  
Phone: +27 81 044 8801

---

*Last updated: July 2026*
