# Contributing to Omgevingsbeleid API

<p align="center">
   <img src="https://avatars.githubusercontent.com/u/60095455?s=400&u=72f83477004260f0a11c119f40f27f30c6e4a12c&v=4" alt="Provincie Zuid-Holland" width="300">
</p>

Thank you for your interest in contributing to the Omgevingsbeleid API project! This document provides guidelines and instructions for contributing to this government policy management system.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)
- [Security](#security)

## Code of Conduct

As a government project serving the Province of Zuid-Holland, we maintain high standards of professionalism and collaboration. We expect all contributors to:

- Be respectful and inclusive in all interactions
- Provide constructive feedback
- Focus on what is best for the community and public service
- Show empathy towards other contributors
- Respect differing viewpoints and experiences

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.13+ installed (preferably via `pyenv`)
- Git configured with your GitHub account
- Familiarity with the project's [README](README.md)
- Understanding of the Dutch Environmental Act (Omgevingswet) context is helpful but not required

### Setting Up Your Development Environment

1. **Fork the repository**
   
   Click the "Fork" button on the [GitHub repository](https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-API) page.

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Omgevingsbeleid-API.git
   cd Omgevingsbeleid-API
   ```

3. **Add the upstream remote**
   ```bash
   git remote add upstream https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-API.git
   git fetch upstream
   ```

4. **Set up the development environment**
   ```bash
   # Create and activate virtual environment
   make prepare-env
   source .venv/bin/activate
   
   # Copy and configure environment variables
   cp .env.example .env
   # Edit .env with your local settings
   
   # Initialize the database
   make init-database
   make load-fixtures  # Optional: load sample data
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

## Development Process

### Branch Naming Convention

Use descriptive branch names following these patterns:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions or modifications

### Workflow

1. **Stay synchronized with upstream**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow the existing code style and patterns
   - Add or update tests as needed
   - Update documentation if applicable

3. **Validate your changes**
   ```bash
   # Format and lint your code
   make fix
   
   # Run tests
   make test
   
   # Check for any issues
   make check
   ```

## Coding Standards

### Python Style Guide

We use [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting with the following configuration:

- Line length: 120 characters
- Python 3.13+ features are allowed
- Follow PEP 8 with project-specific exceptions (see `pyproject.toml`)

### Code Quality Requirements

1. **Type Hints**
   - Use type hints for all function signatures
   - Utilize Pydantic models for data validation

2. **Documentation**
   - Use clear, descriptive variable and function names
   - Include inline comments for complex logic

3. **Error Handling**
   - Use appropriate exception handling
   - Provide meaningful error messages
   - Log errors appropriately

4. **Security**
   - Never commit sensitive data (passwords, API keys, personal data)
   - Use environment variables for configuration
   - Follow OWASP guidelines for web security

## Testing Requirements

### Test Coverage

- Maintain or improve the existing test coverage
- All new features must include comprehensive tests
- Bug fixes should include regression tests

### Running Tests

```bash
# Run all tests
make test

# Run with verbose output
make testx

# Run specific test
make testcase case=test_name

# Run with coverage report
python -m pytest --cov=app --cov-report=html
```

### Writing Tests

- Place tests in the `app/tests/` directory
- Follow the existing test structure
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases

## Submitting Changes

### Pre-submission Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally (`make test`)
- [ ] Code is properly formatted (`make fix`)
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up-to-date with `main`

### Pull Request Process

1. **Create a Pull Request**
   - Use a clear, descriptive title
   - Start your PR title with one of these prefixes:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `docs`: for documentation changes
     - `style`: for code style changes (formatting, etc.)
     - `refactor`: for code refactoring
     - `test`: for test additions or modifications
     - `chore:` for maintenance tasks (dependencies, etc.)
   - Example: `feat: Add validation for DSO export packages`
   - Reference any related issues (e.g., "Fixes #123")
   - Provide a detailed description of changes

2. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of what this PR does.
   
   ## Type of Change
   - [ ] Bug fix (non-breaking change)
   - [ ] New feature (non-breaking change)
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Related Issues
   Closes #(issue number)
   
   ## Testing
   - [ ] Tests pass locally
   - [ ] New tests added/updated
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No sensitive data exposed
   ```

3. **Code Review**
   - Be responsive to feedback
   - Make requested changes promptly
   - Discuss any disagreements constructively

### Commit Message Guidelines

Follow the conventional commits specification:

```
type: description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

Example:
```
feat: add DSO export validation

Added validation for DSO-compliant export packages to ensure
all required fields are present before publication.

Closes #45
```

## Issue Reporting

### Creating Issues

When creating an issue, please include:

1. **Bug Reports**
   - Clear description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages and stack traces

2. **Feature Requests**
   - Clear description of the feature
   - Use case and benefits
   - Proposed implementation (if applicable)
   - Alternative solutions considered

### Issue Labels

We use labels to categorize issues:
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `critical` - Critical issues affecting production

## Security

### Reporting Security Vulnerabilities

**Do not report security vulnerabilities through public GitHub issues.**

Instead, please report them directly to the security team:
- Email: jm.moos@pzh.nl
- Use our responsible disclosure process

### Security Best Practices

When contributing:
- Never commit credentials or sensitive data
- Use parameterized queries to prevent SQL injection
- Validate and sanitize all user inputs
- Keep dependencies updated
- Follow the principle of least privilege

## Getting Help

If you need help:

1. Check the [README](README.md) and existing documentation
2. Search [existing issues](https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-API/issues)
3. Create a new issue with the `question` label

## Recognition

We value all contributions to this project.

## Resources

- [Project README](README.md)
- [API Documentation](http://localhost:8000/docs) (when running locally)
- [Dutch Environmental Act (Omgevingswet)](https://www.rijksoverheid.nl/onderwerpen/omgevingswet)
- [DSO Documentation](https://aandeslagmetdeomgevingswet.nl/digitaal-stelsel/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)

---

Thank you for contributing to better environmental policy management for Zuid-Holland!

**Provincie Zuid-Holland**  
*Building sustainable environmental policies for the future*
