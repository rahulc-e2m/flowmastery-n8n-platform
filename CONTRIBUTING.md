# Contributing to FlowMastery

First off, thank you for considering contributing to FlowMastery! It's people like you that make FlowMastery such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots and animated GIFs** if possible
* **Include your environment details** (OS, Node version, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior** and **explain which behavior you expected to see instead**
* **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `develop`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Process

### Setting Up Your Development Environment

1. **Fork and clone the repository**
```bash
git clone https://github.com/yourusername/flowMastery.git
cd flowMastery
```

2. **Install dependencies**
```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd packages/frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the development servers**
```bash
# From root directory
npm run dev
```

### Branch Naming Convention

* `feature/` - New features (e.g., `feature/add-oauth-login`)
* `bugfix/` - Bug fixes (e.g., `bugfix/fix-memory-leak`)
* `hotfix/` - Urgent fixes for production (e.g., `hotfix/security-patch`)
* `docs/` - Documentation updates (e.g., `docs/update-api-docs`)
* `refactor/` - Code refactoring (e.g., `refactor/optimize-queries`)
* `test/` - Test additions or fixes (e.g., `test/add-unit-tests`)

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
* `feat`: A new feature
* `fix`: A bug fix
* `docs`: Documentation only changes
* `style`: Changes that don't affect code meaning (formatting, etc.)
* `refactor`: Code change that neither fixes a bug nor adds a feature
* `perf`: Code change that improves performance
* `test`: Adding or correcting tests
* `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(auth): add OAuth2 login support

Implemented Google and GitHub OAuth2 providers with proper
token refresh mechanism and secure storage.

Closes #123
```

### Code Style

#### TypeScript/JavaScript
* Use ESLint and Prettier configurations provided
* Run `npm run lint` before committing
* Use meaningful variable and function names
* Add JSDoc comments for public APIs

#### Python
* Follow PEP 8
* Use Black for formatting (`black app tests`)
* Use type hints where applicable
* Add docstrings to all functions and classes

### Testing

#### Frontend Testing
```bash
cd packages/frontend

# Run unit tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

#### Backend Testing
```bash
cd packages/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Documentation

* Update README.md if you change installation or usage instructions
* Add/update API documentation for new endpoints
* Include inline comments for complex logic
* Update type definitions when changing interfaces

## Review Process

1. **Automated Checks**: All PRs must pass CI/CD checks
2. **Code Review**: At least one maintainer review required
3. **Testing**: All tests must pass
4. **Documentation**: Must be updated if applicable

## Release Process

We use semantic versioning (SemVer):

* **MAJOR** version for incompatible API changes
* **MINOR** version for backwards-compatible functionality additions
* **PATCH** version for backwards-compatible bug fixes

## Questions?

Feel free to open an issue with the `question` label or reach out on our Discord server.

## Recognition

Contributors will be recognized in our README.md and CONTRIBUTORS.md files.

Thank you for contributing to FlowMastery! 🚀
