# PrinterMonitor Pro - API Documentation

Complete API reference for integrating with PrinterMonitor Pro programmatically.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Rate Limits](#rate-limits)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Printers](#printers)
  - [Metrics](#metrics)
  - [Devices](#devices)
  - [Remote Subnets](#remote-subnets)
- [Webhooks](#webhooks)
- [SDKs & Libraries](#sdks--libraries)
- [Code Examples](#code-examples)

---

## Overview

The PrinterMonitor Pro API is a RESTful API that allows you to:
- 📊 Retrieve printer metrics and status
- 🖨️ Register and manage printers
- 📱 Manage proxy devices
- 🌐 Configure remote subnets
- 📈 Access historical data

**API Version:** v1  
**Base URL:** `https://api.prntr.org/api/v1`  
**Format:** JSON  
**Protocol:** HTTPS only

---

## Authentication

PrinterMonitor Pro uses two authentication methods:

### 1. JWT Tokens (For User Actions)

Used for dashboard and user-initiated actions.

**Getting a Token:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Using the Token:**
```http
GET /api/v1/printers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Expiry:** 7 days

### 2. API Keys (For Proxy Devices)

Used by proxy devices to send metrics.

**Format:** `pm_device_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Using an API Key:**
```http
POST /api/v1/printers
X-API-Key: pm_device_kKWj8YiZQ1e94iVK_lOsePHXgXc5QKJ68QjG-A1Qd5U
Content-Type: application/json
```

**Getting an API Key:**
- Log into dashboard
- Go to Settings → Proxy Devices
- Click "Add Device"
- Copy the generated API key

⚠️ **Security:** Never commit API keys to version control or expose them publicly.

---

## Base URL

All API requests must be made to:
```
https://api.prntr.org/api/v1
```

**Example:**
```
https://api.prntr.org/api/v1/printers
https://api.prntr.org/api/v1/metrics/summary
```

---

## Rate Limits

To ensure fair usage and system stability:

| Authentication | Requests/Hour | Requests/Day |
|---------------|---------------|--------------|
| JWT Token | 1,000 | 10,000 |
| API Key (Device) | 500 | 5,000 |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

**Exceeded Rate Limit:**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Rate limit exceeded. Try again in 3600 seconds."
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no response body |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (contact support) |

### Common Errors

**Invalid Authentication:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Resource Not Found:**
```json
{
  "detail": "Printer not found"
}
```

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "ip"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Endpoints

### Authentication Endpoints

#### Register User

Create a new user account.
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Login

Authenticate and get access token.
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User

Retrieve authenticated user information.
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "license": {
    "tier_id": "pro",
    "status": "active",
    "trial_ends_at": null,
    "expires_at": "2026-03-21T00:00:00"
  }
}
```

---

### Printers

#### List All Printers

Get all printers for the authenticated user.
```http
GET /api/v1/printers
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "ip": "192.168.1.100",
    "name": "Office Printer",
    "location": "Building A - Floor 2",
    "model": "HP LaserJet Pro M404n",
    "connection_status": "connected",
    "last_seen_at": "2026-02-20T10:30:00",
    "created_at": "2026-02-15T09:00:00"
  },
  {
    "id": 2,
    "ip": "192.168.1.101",
    "name": "Marketing Printer",
    "location": "Building A - Floor 3",
    "model": "Canon imageRUNNER",
    "connection_status": "connected",
    "last_seen_at": "2026-02-20T10:29:45",
    "created_at": "2026-02-15T09:15:00"
  }
]
```

#### Get Single Printer

Retrieve details for a specific printer.
```http
GET /api/v1/printers/{printer_id}
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": 1,
  "ip": "192.168.1.100",
  "name": "Office Printer",
  "location": "Building A - Floor 2",
  "model": "HP LaserJet Pro M404n",
  "connection_status": "connected",
  "last_seen_at": "2026-02-20T10:30:00",
  "created_at": "2026-02-15T09:00:00"
}
```

#### Register Printer

Manually register a new printer (requires device API key).
```http
POST /api/v1/printers
X-API-Key: pm_device_{key}
Content-Type: application/json

{
  "ip": "192.168.1.100",
  "name": "Office Printer",
  "location": "Building A - Floor 2",
  "model": "HP LaserJet Pro M404n"
}
```

**Response (201):**
```json
{
  "id": 1,
  "ip": "192.168.1.100",
  "name": "Office Printer",
  "location": "Building A - Floor 2",
  "model": "HP LaserJet Pro M404n",
  "connection_status": "connected",
  "last_seen_at": null,
  "created_at": "2026-02-20T10:00:00"
}
```

#### Update Printer

Update printer information.
```http
PATCH /api/v1/printers/{printer_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New Printer Name",
  "location": "Building B - Floor 1"
}
```

**Response (200):**
```json
{
  "id": 1,
  "ip": "192.168.1.100",
  "name": "New Printer Name",
  "location": "Building B - Floor 1",
  "model": "HP LaserJet Pro M404n",
  "connection_status": "connected",
  "last_seen_at": "2026-02-20T10:30:00",
  "created_at": "2026-02-15T09:00:00"
}
```

#### Delete Printer

Remove a printer and all its metrics.
```http
DELETE /api/v1/printers/{printer_id}
Authorization: Bearer {token}
```

**Response (204):** No content

⚠️ **Warning:** This permanently deletes the printer and all historical metrics data.

---

### Metrics

#### Get Metrics Summary

Get latest metrics for all printers (dashboard view).
```http
GET /api/v1/metrics/summary
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "printer_id": 1,
    "printer_name": "Office Printer",
    "printer_ip": "192.168.1.100",
    "location": "Building A - Floor 2",
    "model": "HP LaserJet Pro M404n",
    "connection_status": "connected",
    "latest_metrics": {
      "timestamp": "2026-02-20T10:30:00",
      "total_pages": 12450,
      "toner_level_pct": 65,
      "drum_level_pct": 80,
      "device_status": 0
    }
  }
]
```

#### Get Printer Metrics History

Retrieve historical metrics for a specific printer.
```http
GET /api/v1/metrics/{printer_id}?days=7
Authorization: Bearer {token}
```

**Query Parameters:**
- `days` (optional) - Number of days of history (default: 7, max depends on plan)

**Response (200):**
```json
[
  {
    "id": 1,
    "printer_id": 1,
    "timestamp": "2026-02-20T10:30:00",
    "total_pages": 12450,
    "toner_level_pct": 65,
    "drum_level_pct": 80,
    "device_status": 0
  },
  {
    "id": 2,
    "printer_id": 1,
    "timestamp": "2026-02-20T10:25:00",
    "total_pages": 12448,
    "toner_level_pct": 65,
    "drum_level_pct": 80,
    "device_status": 0
  }
]
```

#### Submit Metrics

Submit new metrics data (requires device API key).
```http
POST /api/v1/metrics
X-API-Key: pm_device_{key}
Content-Type: application/json

{
  "printer_ip": "192.168.1.100",
  "total_pages": 12450,
  "toner_level_pct": 65,
  "drum_level_pct": 80,
  "device_status": 0
}
```

**Response (201):**
```json
{
  "id": 1,
  "printer_id": 1,
  "timestamp": "2026-02-20T10:30:00",
  "total_pages": 12450,
  "toner_level_pct": 65,
  "drum_level_pct": 80,
  "device_status": 0
}
```

---

### Devices

#### List Devices

Get all proxy devices.
```http
GET /api/v1/devices
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Office Raspberry Pi",
    "status": "online",
    "version": "1.0.0",
    "created_at": "2026-02-15T09:00:00",
    "last_seen_at": "2026-02-20T10:30:00"
  }
]
```

#### Register Device

Create a new proxy device and get API key.
```http
POST /api/v1/devices/register
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Office Raspberry Pi",
  "version": "1.0.0"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Office Raspberry Pi",
  "api_key": "pm_device_kKWj8YiZQ1e94iVK_lOsePHXgXc5QKJ68QjG-A1Qd5U",
  "created_at": "2026-02-20T10:00:00"
}
```

⚠️ **Important:** The `api_key` is only returned once. Store it securely!

---

### Remote Subnets

#### List Remote Subnets

Get all configured remote subnets.
```http
GET /api/v1/remote-subnets
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "subnet": "192.168.2.0/24",
    "description": "Building B Network",
    "device_id": 1,
    "enabled": true,
    "created_at": "2026-02-20T09:00:00",
    "last_scanned_at": "2026-02-20T10:00:00"
  }
]
```

#### Add Remote Subnet

Configure a new subnet to scan.
```http
POST /api/v1/remote-subnets
Authorization: Bearer {token}
Content-Type: application/json

{
  "subnet": "192.168.2.0/24",
  "description": "Building B Network",
  "device_id": 1
}
```

**Response (201):**
```json
{
  "id": 1,
  "subnet": "192.168.2.0/24",
  "description": "Building B Network",
  "device_id": 1,
  "enabled": true,
  "created_at": "2026-02-20T10:00:00",
  "last_scanned_at": null
}
```

#### Update Remote Subnet

Modify subnet configuration.
```http
PATCH /api/v1/remote-subnets/{subnet_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "enabled": false,
  "description": "Building B Network (Disabled)"
}
```

**Response (200):**
```json
{
  "id": 1,
  "subnet": "192.168.2.0/24",
  "description": "Building B Network (Disabled)",
  "device_id": 1,
  "enabled": false,
  "created_at": "2026-02-20T10:00:00",
  "last_scanned_at": "2026-02-20T10:00:00"
}
```

#### Delete Remote Subnet

Remove a subnet configuration.
```http
DELETE /api/v1/remote-subnets/{subnet_id}
Authorization: Bearer {token}
```

**Response (204):** No content

---

## Webhooks

*Coming soon!*

Webhooks will allow you to receive real-time notifications for events:
- 🔔 Low toner alerts
- 🔌 Printer offline/online
- 📄 High page count reached
- 🆕 New printer discovered

---

## SDKs & Libraries

### Official SDKs

*Coming soon!*

We're working on official SDKs for:
- Python
- JavaScript/TypeScript (Node.js)
- Go

### Community Libraries

Check [GitHub](https://github.com/printmonitor) for community-contributed clients.

---

## Code Examples

### Python

#### Get All Printers
```python
import requests

API_URL = "https://api.prntr.org/api/v1"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

response = requests.get(f"{API_URL}/printers", headers=headers)
printers = response.json()

for printer in printers:
    print(f"{printer['name']}: {printer['ip']} - Toner: {printer.get('toner_level_pct', 'N/A')}%")
```

#### Register Printer (with Device API Key)
```python
import requests

API_URL = "https://api.prntr.org/api/v1"
DEVICE_KEY = "pm_device_your_key_here"

headers = {
    "X-API-Key": DEVICE_KEY,
    "Content-Type": "application/json"
}

data = {
    "ip": "192.168.1.100",
    "name": "Office Printer",
    "location": "Building A",
    "model": "HP LaserJet Pro"
}

response = requests.post(f"{API_URL}/printers", headers=headers, json=data)
printer = response.json()

print(f"Printer registered: {printer['name']} (ID: {printer['id']})")
```

#### Submit Metrics
```python
import requests
from datetime import datetime

API_URL = "https://api.prntr.org/api/v1"
DEVICE_KEY = "pm_device_your_key_here"

headers = {
    "X-API-Key": DEVICE_KEY,
    "Content-Type": "application/json"
}

metrics = {
    "printer_ip": "192.168.1.100",
    "total_pages": 12500,
    "toner_level_pct": 62,
    "drum_level_pct": 78,
    "device_status": 0
}

response = requests.post(f"{API_URL}/metrics", headers=headers, json=metrics)

if response.status_code == 201:
    print("✓ Metrics submitted successfully")
else:
    print(f"✗ Error: {response.json()}")
```

### JavaScript (Node.js)

#### Get Metrics Summary
```javascript
const axios = require('axios');

const API_URL = 'https://api.prntr.org/api/v1';
const TOKEN = 'your-jwt-token';

async function getMetricsSummary() {
  try {
    const response = await axios.get(`${API_URL}/metrics/summary`, {
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    });
    
    response.data.forEach(printer => {
      console.log(`${printer.printer_name}: Toner ${printer.latest_metrics?.toner_level_pct || 'N/A'}%`);
    });
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

getMetricsSummary();
```

### cURL

#### Login
```bash
curl -X POST https://api.prntr.org/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

#### Get Printers
```bash
curl https://api.prntr.org/api/v1/printers \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Register Printer
```bash
curl -X POST https://api.prntr.org/api/v1/printers \
  -H "X-API-Key: pm_device_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "name": "Office Printer",
    "location": "Building A",
    "model": "HP LaserJet Pro"
  }'
```

---

## Best Practices

### Security

- ✅ **Always use HTTPS** - Never make requests over HTTP
- ✅ **Store credentials securely** - Use environment variables or secret managers
- ✅ **Rotate API keys** - Regenerate periodically
- ✅ **Use least privilege** - Device keys can only access device endpoints
- ✅ **Don't log sensitive data** - Avoid logging tokens/keys

### Performance

- ✅ **Respect rate limits** - Implement exponential backoff
- ✅ **Cache responses** - Don't request same data repeatedly
- ✅ **Use webhooks** - More efficient than polling (when available)
- ✅ **Batch operations** - Submit multiple metrics in one request

### Error Handling
```python
import requests
import time

def make_api_request(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                retry_after = int(e.response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
            elif e.response.status_code >= 500:  # Server error
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## Support

### Need Help?

- 📖 **Documentation:** [User Guide](user-guide.md) | [Installation](installation.md)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/printmonitor/printermonitor-pro/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/printmonitor/printermonitor-pro/discussions)
- 📧 **Email:** support@prntr.org *(coming soon)*

### API Status

Check API uptime and incidents:
- Status Page: *(coming soon)*
- Current Status: ✅ Operational

---

<div align="center">

**API Documentation v1.0** • Last Updated: February 2026

[Main Documentation](../README.md) • [User Guide](user-guide.md) • [Installation Guide](installation.md)

</div>
