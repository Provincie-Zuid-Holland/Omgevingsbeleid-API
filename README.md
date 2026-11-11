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

- [uv](https://docs.astral.sh/uv/) (installs Python 3.13+ for you)
- PostgreSQL, or SQLite with SpatiaLite for local development and tests
- Docker (optional, to run the API together with PostgreSQL)
- Unix-based operating system (Linux/macOS)

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-API.git
   cd Omgevingsbeleid-API
   ```

2. **Install uv and SpatiaLite**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   sudo apt install libsqlite3-mod-spatialite   # Debian/Ubuntu/Mint
   ```

3. **Install Python and all dependencies**
   ```bash
   uv sync
   ```

   This downloads the Python version from `.python-version` if needed, creates `.venv/` and installs
   all runtime and development dependencies from `uv.lock`. You don't need to activate the venv:
   `make` commands and `uv run` use it automatically.

   On Linux, uv's Python supports loadable SQLite extensions out of the box, so SpatiaLite works without
   compiling Python yourself. On macOS, uv's Python lacks this support; point uv at a Python that has it
   (for example Homebrew's) with `uv python pin <path-to-python>`.

   To verify SpatiaLite works:
   ```bash
   uv run python -c "import sqlite3; c = sqlite3.connect(':memory:'); c.enable_load_extension(True); c.load_extension('mod_spatialite'); print(c.execute('select spatialite_version()').fetchone())"
   ```

4. **Configure environment**
   
   Copy the example environment file and configure:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration. For development with SQLite:
   ```env
   LOCAL_DEVELOPMENT_MODE=True
   SQLALCHEMY_DATABASE_URI="sqlite+pysqlite:///api.db"
   SECRET_KEY="your-secret-key-here"
   ```

5. **Initialize database**
   ```bash
   # Run migrations
   uv run alembic upgrade head
   
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
   uv run uvicorn app.main:app --reload
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
├── pyproject.toml         # Project metadata, dependencies and tool settings
├── uv.lock                # Locked dependency versions (commit together with pyproject.toml)
└── .python-version        # Python version used by uv
```

### Available Commands

Run `make` to list all commands. The most common ones:

```bash
# Development
make run                  # Start the development server
make debug                # Start with debugging enabled
make format               # Format code with Ruff
make check                # Lint and check formatting without fixing
make fix                  # Fix linting issues and format

# Database Management
make init-database        # Initialize database schema
make drop-database        # Drop all database tables
make load-fixtures        # Load sample data
make reset-test-database  # Reset database with fixtures
```

For Docker commands, see [Running with Docker](#running-with-docker).

### Managing Dependencies

Dependencies are defined in `pyproject.toml` and locked in `uv.lock`. Always commit both files together.

```bash
uv add <package>                      # Add a runtime dependency
uv add --dev <package>                # Add a development-only dependency (tests, linting)
uv remove <package>                   # Remove a dependency
uv lock --upgrade                     # Upgrade all dependencies within their version ranges
uv lock --upgrade-package <package>   # Upgrade a single package
uv tree                               # Show the dependency tree
```

`uv add`, `uv remove` and `uv run` keep `.venv` in sync automatically. Run `uv sync` yourself after
cloning, or after switching branches when you work in an activated venv (`source .venv/bin/activate`).

To change the Python version: `uv python pin 3.14`, then `uv sync`.

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
| `LOCAL_DEVELOPMENT_MODE` | Enable local development features | `False` |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | - |
| `SECRET_KEY` | JWT secret key for authentication | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `240` |
| `MAIN_CONFIG_FILE` | Path to main configuration | `./config/main.yml` |
| `OBJECT_CONFIG_PATH` | Path to object configurations | `./config/objects/` |

### Database Configuration

The database is configured with `SQLALCHEMY_DATABASE_URI`.

**PostgreSQL**:
```env
SQLALCHEMY_DATABASE_URI="postgresql+psycopg://omgevingsbeleid:your-password@localhost:5432/omgevingsbeleid"
```

**SQLite (local development and tests)**:
```env
SQLALCHEMY_DATABASE_URI="sqlite+pysqlite:///api.db"
```

### Running with Docker

The Docker setup runs the API together with a PostgreSQL database:

```bash
make docker-init     # Build and start the services, then run migrations
make docker-psql     # Open a psql shell on the database
make docker-down     # Stop the services and remove their volumes
```

Run `make` for all Docker commands, such as loading fixtures or creating Alembic migrations inside the container.

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
- **Database**: PostgreSQL (SQLite with SpatiaLite for development and tests)
- **Migrations**: Alembic
- **Validation**: Pydantic 2.0
- **Authentication**: JWT (python-jose)
- **Geospatial**: GeoPandas, Shapely
- **Code Quality**: Ruff (linting & formatting)
- **Packaging**: uv (dependencies, virtualenv and Python version)

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
make testcov                 # Run with coverage (XML report)
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
