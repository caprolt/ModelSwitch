# Security Policy

## Supported Versions

We actively support the following versions of ModelSwitch with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do Not Open a Public Issue

Please **do not** create a public GitHub issue for security vulnerabilities. Public disclosure before a fix is available can put all users at risk.

### 2. Report Privately

Report security vulnerabilities by emailing: **[security@modelswitch.dev]** (or create a private security advisory on GitHub)

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity (typically 30-90 days)

## Security Best Practices

When deploying ModelSwitch in production, follow these security guidelines:

### 1. Authentication & Authorization

ModelSwitch does not include built-in authentication. **Always** deploy behind an authentication layer:

```bash
# Example: Use an API gateway with authentication
# - Kong
# - Tyk
# - AWS API Gateway
# - Azure API Management
```

### 2. Network Security

- **Isolate Admin Endpoints**: Use network policies to restrict admin endpoint access
- **Use TLS/HTTPS**: Always encrypt traffic in production
- **Firewall Rules**: Restrict access to necessary ports only

### 3. Input Validation

While ModelSwitch validates input types, additional validation is recommended:

```python
# Implement custom validation for your use case
def validate_business_logic(features):
    # Example: Check feature ranges
    if any(f < 0 or f > 100 for f in features):
        raise ValueError("Features out of expected range")
```

### 4. Rate Limiting

Implement rate limiting to prevent abuse:

```python
# Example with FastAPI
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("100/minute")
async def predict(request: Request, ...):
    ...
```

### 5. Model Security

- **Validate Model Files**: Only load models from trusted sources
- **Scan for Malware**: Use antivirus/malware scanning on model files
- **Access Control**: Restrict who can upload/modify models
- **Model Signing**: Consider signing models to verify authenticity

### 6. Secrets Management

Never commit secrets to version control:

```bash
# Use environment variables
export API_KEY=your-secret-key

# Or use secret management tools
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
```

### 7. Container Security

```dockerfile
# Use specific base image versions (not 'latest')
FROM python:3.11.6-slim

# Run as non-root user
USER app

# Scan containers regularly
# Use tools like Trivy, Clair, or Snyk
```

### 8. Logging & Monitoring

- **Log Security Events**: Authentication failures, admin actions
- **Monitor Anomalies**: Unusual request patterns, error rates
- **Set Up Alerts**: High error rates, unauthorized access attempts

### 9. Dependencies

Keep dependencies updated:

```bash
# Check for vulnerabilities
pip install safety
safety check

# Update regularly
pip install --upgrade -r requirements.txt
```

### 10. Regular Security Audits

- Review access logs regularly
- Conduct security assessments
- Penetration testing for production systems
- Code reviews for security implications

## Known Security Considerations

### Current Limitations

1. **No Built-in Authentication**: Designed to be deployed behind an authenticated gateway
2. **No Rate Limiting**: Should be implemented at the infrastructure level
3. **No Audit Logging**: Consider adding for compliance requirements
4. **Model Pickle Files**: Python pickle files can execute arbitrary code - only use trusted models

### Planned Security Enhancements

- [ ] Optional API key authentication
- [ ] Built-in rate limiting
- [ ] Audit logging for admin operations
- [ ] Model validation and sandboxing
- [ ] RBAC (Role-Based Access Control)

## Security Checklist for Production

Before deploying to production, verify:

- [ ] Application behind authenticated API gateway
- [ ] TLS/HTTPS enabled
- [ ] Network policies restricting admin endpoints
- [ ] Rate limiting configured
- [ ] Logging and monitoring in place
- [ ] Secrets managed securely (not in code)
- [ ] Dependencies up to date
- [ ] Container images scanned for vulnerabilities
- [ ] Firewall rules configured
- [ ] Backup and disaster recovery plan
- [ ] Security incident response plan
- [ ] Regular security updates scheduled

## Security Updates

Security patches are released as soon as possible after a vulnerability is confirmed. Users will be notified via:

1. GitHub Security Advisories
2. Release notes
3. Email (if registered)

## Responsible Disclosure

We appreciate the security research community's efforts in keeping ModelSwitch secure. We will:

- Acknowledge your contribution
- Keep you informed of progress
- Credit you in release notes (if desired)
- Work with you to understand and fix the issue

## Bug Bounty Program

Currently, we do not have a formal bug bounty program. However, we deeply appreciate security reports and will acknowledge contributors publicly (with permission).

## Contact

For security concerns:
- **Email**: security@modelswitch.dev
- **GitHub**: [Create a private security advisory](https://github.com/caprolt/ModelSwitch/security/advisories/new)

For general questions:
- **GitHub Issues**: https://github.com/caprolt/ModelSwitch/issues
- **Discussions**: https://github.com/caprolt/ModelSwitch/discussions

---

Thank you for helping keep ModelSwitch and its users safe!
