# Contributing to Dataverse SDK

Thank you for your interest in contributing to the Dataverse SDK! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/dataverse-sdk.git
   cd dataverse-sdk
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify setup**
   ```bash
   # Run tests
   pytest tests/unit/
   
   # Run linting
   black --check dataverse_sdk/
   flake8 dataverse_sdk/
   mypy dataverse_sdk/
   ```

## 📝 Development Workflow

### 1. Create a Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run with coverage
pytest tests/unit/ --cov=dataverse_sdk --cov-report=html

# Test CLI functionality
dv-cli --help
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add bulk upsert operation

- Implement bulk upsert functionality
- Add comprehensive tests
- Update documentation
- Closes #123"
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## 📋 Contribution Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting  
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security analysis

Run all checks:
```bash
# Format code
black dataverse_sdk/ tests/ cli/ examples/
isort dataverse_sdk/ tests/ cli/ examples/

# Check linting
flake8 dataverse_sdk/ tests/ cli/ examples/

# Type checking
mypy dataverse_sdk/

# Security check
bandit -r dataverse_sdk/
```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**
```
feat(auth): add device code authentication flow
fix(client): handle rate limiting correctly
docs: update README with new examples
test(models): add tests for QueryOptions validation
```

### Testing Guidelines

#### Unit Tests
- Write tests for all new functionality
- Aim for >90% code coverage
- Use descriptive test names
- Include docstrings for complex tests

```python
def test_account_creation_with_valid_data():
    """Test that account creation works with valid data."""
    # Arrange
    account_data = {"name": "Test Account"}
    
    # Act
    result = create_account(account_data)
    
    # Assert
    assert result.success is True
    assert result.account_id is not None
```

#### Integration Tests
- Test real API interactions
- Use test environment credentials
- Clean up test data
- Mark as slow tests: `@pytest.mark.slow`

#### CLI Tests
- Test command-line interface
- Verify help text and options
- Test error handling

### Documentation

#### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints for all parameters and return values

```python
async def create_entity(
    self,
    entity_type: str,
    data: Dict[str, Any],
    return_record: bool = False
) -> Union[str, Dict[str, Any]]:
    """Create a new entity in Dataverse.
    
    Args:
        entity_type: The logical name of the entity type.
        data: Dictionary containing the entity data.
        return_record: Whether to return the created record.
        
    Returns:
        Entity ID if return_record is False, otherwise the full entity record.
        
    Raises:
        ValidationError: If the entity data is invalid.
        APIError: If the API request fails.
        
    Example:
        >>> account_id = await sdk.create("accounts", {"name": "Test"})
        >>> print(account_id)
        "12345678-1234-1234-1234-123456789012"
    """
```

#### README Updates
- Update README.md for new features
- Add usage examples
- Update table of contents if needed

#### Changelog
- Add entries to CHANGELOG.md
- Follow [Keep a Changelog](https://keepachangelog.com/) format

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Minimal steps to reproduce the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: Python version, OS, SDK version
6. **Code sample**: Minimal code that reproduces the issue

Use the bug report template:

```markdown
## Bug Description
Brief description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- Python version: 3.11.0
- OS: Ubuntu 22.04
- SDK version: 1.0.0

## Code Sample
```python
# Minimal code that reproduces the issue
```

## Additional Context
Any other relevant information.
```

## 💡 Feature Requests

For feature requests, please:

1. Check if the feature already exists
2. Search existing issues and discussions
3. Provide a clear use case
4. Describe the proposed solution
5. Consider implementation complexity

Use the feature request template:

```markdown
## Feature Description
Clear description of the proposed feature.

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches did you consider?

## Additional Context
Any other relevant information.
```

## 🔍 Code Review Process

### For Contributors
- Ensure all tests pass
- Update documentation
- Respond to review feedback promptly
- Keep pull requests focused and small

### For Reviewers
- Be constructive and respectful
- Focus on code quality and maintainability
- Check for test coverage
- Verify documentation updates

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed

## 🏷️ Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Steps
1. Update version in `dataverse_sdk/__init__.py`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`
6. GitHub Actions handles the rest

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Bug fixes
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Medium Priority
- New authentication methods
- Additional entity operations
- CLI enhancements
- Integration examples

### Low Priority
- Code refactoring
- Developer tooling
- CI/CD improvements

## 📚 Resources

### Documentation
- [Microsoft Dataverse Web API](https://docs.microsoft.com/en-us/powerapps/developer/data-platform/webapi/)
- [OData v4.0 Specification](https://www.odata.org/documentation/)
- [Python Async Programming](https://docs.python.org/3/library/asyncio.html)

### Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [pytest Testing Framework](https://pytest.org/)
- [mypy Type Checker](https://mypy.readthedocs.io/)

### Community
- [GitHub Discussions](https://github.com/dataverse-sdk/dataverse-sdk/discussions)
- [Issues](https://github.com/dataverse-sdk/dataverse-sdk/issues)

## 🙏 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

Thank you for contributing to the Dataverse SDK! 🎉

