# Contributing to Lucy Bot Chart Service

Thank you for your interest in contributing to the Lucy Bot Chart Service! This project is licensed under GPL v3+ to comply with the Kerykeion library's licensing requirements.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chart-service-gpl
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the service locally**
   ```bash
   python chart_service.py
   ```

4. **Test the API**
   ```bash
   curl http://localhost:5000/health
   ```

## Making Contributions

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### Testing
- Test your changes with various chart configurations
- Ensure the health endpoint remains functional
- Test error handling for invalid inputs

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### What to Contribute

**Welcome contributions:**
- Bug fixes in chart generation
- Performance improvements
- Better error handling
- Additional chart types or features
- Documentation improvements
- Docker optimizations

**Before contributing large features:**
- Open an issue to discuss the feature first
- Ensure it aligns with the GPL compliance goals
- Consider backward compatibility

## License Compliance

This project is GPL v3+ licensed because:
- It uses the Kerykeion library (GPL v3+)
- All derivative works must maintain GPL compatibility
- Contributions must be compatible with GPL v3+

By contributing, you agree that your contributions will be licensed under GPL v3+.

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide detailed information for bug reports

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

Thank you for contributing to open source astrology software! 🌟