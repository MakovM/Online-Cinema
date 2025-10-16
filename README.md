# Online Cinema 🎬

A modern online cinema platform built with FastAPI for browsing, purchasing, and watching movies.

## 🚀 Features

- **User Management** - Registration, email activation, authentication, and profile management with JWT tokens
- **Movie Catalog** - Browse movies with advanced filtering and pagination by genre, director, stars, and ratings
- **Favorites & Likes** - Save favorite movies, toggle likes on movies and comments
- **Comments** - Write, edit, and delete movie reviews with like functionality
- **Shopping Cart** - Add movies to cart, manage cart items, and clear cart
- **Order Management** - Create orders from cart, view order history, cancel pending orders
- **Payment Integration** - Stripe payment processing support
- **Role-Based Access** - Three-tier access control (Admin, Moderator, User)
- **Email Notifications** - Automated emails for activation, password reset, and order updates
- **Content Management** - Full CRUD operations for movies, genres, stars, and directors (Admin/Moderator)

## 🛠️ Tech Stack

- **Backend**: FastAPI 0.115+, SQLAlchemy 2.0 (async), Pydantic 2.10+
- **Database**: PostgreSQL with asyncpg driver
- **Cache & Queue**: Redis, Celery
- **Storage**: AWS S3 / MinIO (aioboto3)
- **Payment**: Stripe
- **Auth**: JWT (python-jose), bcrypt password hashing
- **Pagination & Filtering**: fastapi-pagination, fastapi-filter
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL (for local development)
- Redis (for local development)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd Online-Cinema
```

2. **Create environment file**
```bash
cp .env.sample .env
```

3. **Configure your `.env` file with essential settings:**
```env
# Database
POSTGRES_DB=movies_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=postgres_cinema
POSTGRES_DB_PORT=5432

# JWT Secrets (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY_ACCESS=your_access_secret_key
SECRET_KEY_REFRESH=your_refresh_secret_key

# Redis
CELERY_BROKER_URL=redis://redis_cinema:6379/0

# Email (MailHog for dev)
EMAIL_HOST=mailhog_cinema
EMAIL_PORT=1025
```

4. **Start the application**
```bash
# Development
docker-compose -f docker-compose-dev.yml up --build

# Production
docker-compose -f docker-compose-prod.yml up --build -d
```

5. **Access the services**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MailHog: http://localhost:8025
- pgAdmin: http://localhost:3333

### Local Development (Without Docker)

1. **Install Poetry**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Install dependencies**
```bash
poetry install
poetry shell
```

3. **Run database migrations**
```bash
alembic upgrade head
```

4. **Start the server**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Start Celery (in separate terminals)**
```bash
# Worker
celery -A src.celery_worker worker --loglevel=info

# Beat scheduler
celery -A src.celery_worker beat --loglevel=info
```

## 📁 Project Structure

```
Online-Cinema/
├── src/
│   ├── routers/          # API endpoints
│   │   ├── accounts.py   # Authentication
│   │   ├── movies.py     # Movie catalog
│   │   ├── comments.py   # Comments & reviews
│   │   ├── carts.py      # Shopping cart
│   │   └── orders.py     # Orders & payments
│   ├── database/
│   │   └── models/       # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── security/         # Auth & JWT
│   ├── tasks/            # Celery tasks
│   └── main.py           # App entry point
├── docker-compose-dev.yml
├── docker-compose-prod.yml
├── Dockerfile
└── pyproject.toml
```

## 🔌 Main API Endpoints

### Authentication & User Management
```
POST   /api/v1/accounts/register              # Register new user
POST   /api/v1/accounts/activate              # Activate account
POST   /api/v1/accounts/resend-activation     # Resend activation email
POST   /api/v1/accounts/login                 # Login
POST   /api/v1/accounts/logout                # Logout (revoke refresh token)
POST   /api/v1/accounts/refresh               # Refresh access token
POST   /api/v1/accounts/password-reset/request         # Request password reset
POST   /api/v1/accounts/reset-password/complete       # Complete password reset
POST   /api/v1/accounts/change-password       # Change password (authenticated)
POST   /api/v1/accounts/change-role           # Change user role (Admin only)
```

### User Profiles
```
GET    /api/v1/profiles/me                    # Get current user profile
POST   /api/v1/profiles/users/{id}/profile    # Create user profile
```

### Movies
```
GET    /api/v1/movies/                        # List movies (with filters & pagination)
POST   /api/v1/movies/                        # Create movie (Admin/Moderator)
GET    /api/v1/movies/{id}                    # Get movie details
PATCH  /api/v1/movies/{id}                    # Update movie (Admin/Moderator)
DELETE /api/v1/movies/{id}                    # Delete movie (Admin/Moderator)
POST   /api/v1/movies/{id}/toggle-like        # Toggle like on movie
```

### Genres
```
GET    /api/v1/movies/genres/                 # List all genres (with movie count)
POST   /api/v1/movies/genres/                 # Create genre (Admin/Moderator)
GET    /api/v1/movies/genres/{id}             # Get movies by genre
PATCH  /api/v1/movies/genres/{id}             # Update genre (Admin/Moderator)
DELETE /api/v1/movies/genres/{id}             # Delete genre (Admin/Moderator)
```

### Stars
```
GET    /api/v1/movies/stars/                  # List all stars
POST   /api/v1/movies/stars/                  # Create star (Admin/Moderator)
GET    /api/v1/movies/stars/{id}              # Get star details
PATCH  /api/v1/movies/stars/{id}              # Update star (Admin/Moderator)
DELETE /api/v1/movies/stars/{id}              # Delete star (Admin/Moderator)
```

### Favorites
```
GET    /api/v1/movies/favorites/              # Get user's favorite movies
POST   /api/v1/movies/favorites/              # Add movie to favorites
DELETE /api/v1/movies/favorites/{movie_id}    # Remove from favorites
```

### Comments
```
POST   /api/v1/comments/                      # Create comment
PATCH  /api/v1/comments/{id}                  # Update comment (owner only)
DELETE /api/v1/comments/{id}                  # Delete comment (owner only)
POST   /api/v1/comments/{id}/toggle-like      # Toggle like on comment
```

### Shopping Cart
```
GET    /api/v1/shopping-carts/cart/                    # Get current user's cart
POST   /api/v1/shopping-carts/cart/{user_id}           # Get user cart (Admin/Moderator)
POST   /api/v1/shopping-carts/cart/items/{id}/add      # Add movie to cart
DELETE /api/v1/shopping-carts/cart/items/{id}/delete   # Remove item from cart
DELETE /api/v1/shopping-carts/cart/clear               # Clear entire cart
```

### Orders
```
POST   /api/v1/orders/                        # Create order from cart
GET    /api/v1/orders/                        # List orders (with filters)
POST   /api/v1/orders/cancel/{id}             # Cancel pending order
```

Visit http://localhost:8000/docs for interactive API documentation.

## 🔍 Filtering & Pagination

The API supports advanced filtering and pagination on movie, genre, and star endpoints:

### Pagination
All list endpoints support pagination with query parameters:
```
GET /api/v1/movies/?page=1&size=20
```

### Movie Filters
Filter movies by various criteria:
```
GET /api/v1/movies/?imdb__gte=7.0&year=2023
GET /api/v1/movies/?genres=Action&order_by=imdb
```

Available filters:
- `name` - Movie name (contains)
- `year` - Release year
- `imdb`, `imdb__gte`, `imdb__lte` - IMDb rating filters
- `price`, `price__gte`, `price__lte` - Price range
- `genres` - Filter by genre name
- `directors` - Filter by director name
- `stars` - Filter by star name
- `order_by` - Sort by field (e.g., `imdb`, `-year` for descending)

## 🗄️ Database Schema

### Main Modules

**Accounts** - Users, profiles, authentication tokens, and roles (Admin, Moderator, User)

**Movies** - Movie catalog with genres, directors, stars, certifications, favorites, comments, and likes

**Shopping** - Shopping carts, cart items, orders, and order items

### Key Relationships
- User ↔ Profile (1:1)
- User → Orders (1:N)
- Movies ↔ Genres/Stars/Directors (N:M)
- User ↔ Favorites (N:M)

### Notable Features
- **Polymorphic Likes** - Like system supports both movies and comments using `likeable_type` and `likeable_id`
- **Price Snapshots** - Order items store `price_at_order` to maintain historical pricing
- **Token Management** - Separate tokens for activation, password reset, and refresh with expiration
- **Unique Constraints** - Movies identified by unique combination of `(name, year, time)`

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific test file
poetry run pytest src/tests/test_movies.py

# Using Docker
docker-compose -f docker-compose-dev.yml exec web pytest
```

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

## 🎨 Code Quality

```bash
# Format code
poetry run black src/
poetry run isort src/

# Linting
poetry run flake8 src/
poetry run mypy src/

# All checks
poetry run black src/ && poetry run isort src/ && poetry run flake8 src/
```

## 🔒 Security

- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt (12 rounds)
- Role-based access control (User, Moderator, Admin)
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM

## 🐛 Common Issues

### Database Connection
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker-compose logs db

# Connect to database
docker-compose exec db psql -U admin -d movies_db
```

### Port Conflicts
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Reset Everything
```bash
# Stop and remove all containers
docker-compose down -v

# Rebuild from scratch
docker-compose -f docker-compose-dev.yml up --build
```

## 📝 Environment Variables

Generate secure keys for JWT:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

See `.env.sample` for all available configuration options.

## 📚 Documentation

- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

This is a learning project created by **REST in Peace Team**.

## 📄 License

MIT License

---

**Made with ❤️ by REST in Peace Team**
