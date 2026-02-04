# Omgevingsbeleid API

<p align="center">
   <img src="https://avatars.githubusercontent.com/u/60095455?s=400&u=72f83477004260f0a11c119f40f27f30c6e4a12c&v=4" alt="Provincie Zuid-Holland" width="400">
</p>

## Overview

The Omgevingsbeleid API is a comprehensive policy management system developed for the Province of Zuid-Holland, Netherlands. This system facilitates the digital management and publication of environmental policies in compliance with the Dutch Environmental Act (Omgevingswet) and integrates with the national Digital System for Environmental Law (DSO - Digitaal Stelsel Omgevingswet).

### Key Features

- **Policy Object Management**: Comprehensive versioning and lifecycle management of policy objects
- **Module System**: Structured workflows for policy development and approval processes  
- **DSO Integration**: Compliance with national publication standards for environmental policies
- **Document Management**: Integrated asset and document handling with version control
- **Publication Pipeline**: Automated generation of DSO-compliant publication packages

## System Requirements

- Python 3.13+
- SQLite with SpatiaLite (development) or Microsoft SQL Server (production)
- Unix-based operating system (Linux/macOS)

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-API.git
   cd Omgevingsbeleid-API
   ```

2. **Set up Python environment**
   
   Ensure you have Python 3.13 installed. We recommend using `pyenv` for version management:
   ```bash
   # If using pyenv
   CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.13
   pyenv local 3.13
   ```

3. **Create virtual environment**
   ```bash
   make prepare-env
   ```
   
   Or manually:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   
   Copy the example environment file and configure:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration. For development with SQLite:
   ```env
   DEBUG_MODE=True
   LOCAL_DEVELOPMENT_MODE=True
   SQLALCHEMY_DATABASE_URI="sqlite+pysqlite:///api.db"
   SECRET_KEY="your-secret-key-here"
   ```

5. **Initialize database**
   ```bash
   # Run migrations
   python -m alembic upgrade head
   
   # Or use the make command
   make init-database
   
   # Optionally load sample data
   make load-fixtures
   ```

6. **Run the application**
   ```bash
   make run
   ```
   
   Or directly with uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

## Development

### Project Structure

```
Omgevingsbeleid-API/
├── app/
│   ├── api/                   # API layer
│   │   ├── domains/           # Domain-driven modules
│   │   │   ├── modules/       # Policy module management
│   │   │   ├── objects/       # Policy objects
│   │   │   ├── publications/  # DSO publication system
│   │   │   ├── users/         # Authentication & authorization
│   │   │   ├── werkingsgebieden/ # Geographic areas
│   │   │   └── others/        # Supporting features
│   │   ├── events/           # Event system
│   │   └── services/         # Cross-cutting services
│   ├── core/                 # Core functionality
│   │   ├── db/              # Database configuration
│   │   ├── tables/          # SQLAlchemy models
│   │   └── settings.py      # Application settings
│   ├── commands/            # CLI commands
│   └── tests/              # Test suite
├── alembic/                # Database migrations
├── config/                 # Configuration files
│   ├── main.yml           # Main configuration
│   └── objects/           # Object type definitions
├── requirements.txt       # Production dependencies
└── requirements-dev.txt   # Development dependencies
```

### Available Commands

```bash
# Development
make run                # Start the development server
make debug             # Start with debugging enabled
make format            # Format code with Ruff
make check             # Lint code without fixing
make fix              # Fix linting issues and format

# Database Management
make init-database     # Initialize database schema
make drop-database     # Drop all database tables
make load-fixtures     # Load sample data
make reset-test-database  # Reset database with fixtures

# Dependency Management
make pip-sync         # Sync dependencies with lock files
make pip-compile      # Regenerate lock files
make pip-upgrade      # Upgrade all dependencies

# Environment Setup
make prepare-env      # Create and setup virtual environment
```

### API Documentation

Once the application is running, you can access:
- **Interactive API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative API Documentation**: `http://localhost:8000/redoc` (ReDoc)

### VS Code Integration

The project includes VS Code launch configurations for debugging:

1. **API: Debug LAN exposed** - Run the API with debugging, accessible from local network
2. **API: Remote Debug** - Attach to a running debug session
3. **API: Current File** - Debug the currently open Python file

To use these, open the project in VS Code and use the Run and Debug panel (F5).

## Configuration

### Environment Variables

Key environment variables (see `app/core/settings.py` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG_MODE` | Enable debug mode | `False` |
| `LOCAL_DEVELOPMENT_MODE` | Enable local development features | `False` |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | - |
| `SECRET_KEY` | JWT secret key for authentication | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `240` |
| `MAIN_CONFIG_FILE` | Path to main configuration | `./config/main.yml` |
| `OBJECT_CONFIG_PATH` | Path to object configurations | `./config/objects/` |

### Database Configuration

The system supports both SQLite (development) and Microsoft SQL Server (production):

**SQLite (Development)**:
```env
SQLALCHEMY_DATABASE_URI="sqlite+pysqlite:///api.db"
```

**SQL Server (Production)**:
```env
DB_HOST=your-server-host
DB_NAME=your-database-name
DB_USER=your-username
DB_PASS=your-password
DB_DRIVER="ODBC Driver 17 for SQL Server"
```

### DSO Integration

For DSO publication features, configure the KOOP services:
```env
PUBLICATION_KOOP__PRE__API_KEY="your-api-key"
PUBLICATION_KOOP__PRE__RENVOOI_API_URL="https://renvooiservice-eto.overheid.nl"
PUBLICATION_KOOP__PRE__PREVIEW_API_URL="https://besluitpreviewservice-eto.overheid.nl"
```

## Architecture

### Technology Stack

- **Framework**: FastAPI (Python 3.13)
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite/Microsoft SQL Server
- **Validation**: Pydantic 2.0
- **Authentication**: JWT (python-jose)
- **Geospatial**: GeoPandas, Shapely
- **Code Quality**: Ruff (linting & formatting)

### Design Patterns

- **Domain-Driven Design**: Clear separation of business domains
- **Repository Pattern**: Abstracted data access layer
- **Dependency Injection**: IoC container for loose coupling
- **Event-Driven**: Event system for cross-domain communication
- **RESTful API**: Following REST principles and OpenAPI specification

## Testing

Run the test suite:
```bash
make test                    # Run all tests
make testx                   # Run with verbose output and stop on first failure
make testcase case=test_name # Run specific test case
```

## License

This project is licensed under the European Union Public Licence (EUPL) v1.2. See [LICENSE.md](LICENSE.md) for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Support

For issues, questions, or contributions, please use the [GitHub Issues](https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-API/issues) page.

## Authors

See [AUTHORS](AUTHORS) file for the list of contributors.

---

**Provincie Zuid-Holland**  
*Building sustainable environmental policies for the future*