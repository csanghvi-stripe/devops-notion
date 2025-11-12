# Contributing to DevOps Flow Bot

Thank you for your interest in contributing to DevOps Flow Bot! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/notion-bot.git
   cd notion-bot
   ```
3. **Set up development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow **PEP 8** style guide for Python code
- Use **type hints** for all function parameters and return values
- Write **descriptive variable names** (avoid single letters except in loops)
- Add **docstrings** to all classes and functions

Example:
```python
def process_webhook(payload: Dict[str, Any]) -> bool:
    """
    Process incoming webhook payload.

    Args:
        payload: Webhook data from GitHub

    Returns:
        True if processed successfully, False otherwise
    """
    pass
```

### Code Organization

- Keep service classes focused on single responsibilities
- Use dependency injection (pass dependencies to constructors)
- Handle errors gracefully with try-except blocks
- Log important events and errors

### Logging

Use the existing logger:
```python
logger.info("Processing PR #123")
logger.warning("Task ID not found")
logger.error(f"Error updating Notion: {e}")
```

## Testing Your Changes

### Manual Testing

1. Set up test environment with `.env` file
2. Run the bot locally:
   ```bash
   python3 bot.py
   ```
3. Use ngrok to expose local server:
   ```bash
   ngrok http 5001
   ```
4. Test with a real PR that includes a task ID

### Verify Health Check

```bash
curl http://localhost:5001/health
```

## Submitting Changes

### Before Submitting

- [ ] Test your changes thoroughly
- [ ] Ensure code follows style guidelines
- [ ] Update documentation if needed
- [ ] Add type hints to new functions
- [ ] Check that all logs are appropriate

### Pull Request Process

1. **Update your branch** with latest main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

   Commit message format:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for improvements
   - `Docs:` for documentation changes

3. **Push to your fork**:
   ```bash
   git push origin your-feature-branch
   ```

4. **Create Pull Request** on GitHub:
   - Provide clear description of changes
   - Reference any related issues
   - Include screenshots if relevant

## Feature Requests & Bug Reports

### Reporting Bugs

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version)
- Relevant logs

### Suggesting Features

Include:
- Clear description of the feature
- Use case / problem it solves
- Proposed implementation (if you have ideas)
- Any potential drawbacks

## Areas for Contribution

We welcome contributions in these areas:

### High Priority
- [ ] Unit tests for service classes
- [ ] Integration tests for webhook flows
- [ ] Error recovery improvements
- [ ] Performance optimizations

### Feature Enhancements
- [ ] Support for multiple repositories
- [ ] Custom workflow configurations
- [ ] Analytics dashboard
- [ ] GitHub issue creation from Notion
- [ ] Jira integration

### Documentation
- [ ] Video tutorials
- [ ] More troubleshooting examples
- [ ] Architecture diagrams
- [ ] API documentation

### DevOps
- [ ] Docker Compose setup
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting

## Questions?

- **General questions**: Open a [Discussion](https://github.com/Cdotsanghvi/notion-bot/discussions)
- **Bug reports**: Open an [Issue](https://github.com/Cdotsanghvi/notion-bot/issues)
- **Security concerns**: Email the maintainer directly (see README)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

Thank you for contributing! 🎉
