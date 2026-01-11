# California Court Scraper

Advanced web scraping system for California court public data with automatic token rotation, concurrent processing, and MongoDB storage.

## Features

- **SOLID Architecture**: Clean separation of concerns with services, managers, processors, and repositories
- **Automatic Token Rotation**: Refreshes authentication tokens every 10 minutes
- **Captcha Buffer System**: Maintains 2 pre-solved captchas to avoid scraping interruptions
- **Concurrent Processing**: Processes 3 cases simultaneously, each downloading 5 documents in parallel
- **Retry Mechanism**: Automatic retry with configurable attempts for failed requests
- **MongoDB Storage**: Stores complete case data with embedded PDF documents
- **Colored Logging**: Clear, informative console output with progress tracking
- **Proxy Support**: Optional proxy configuration for case data requests

## Architecture

```
├── services/              # Core business logic
│   ├── captcha_service.py    # reCAPTCHA v2 solving
│   ├── token_service.py      # Token retrieval
│   ├── case_service.py       # Case data fetching
│   └── document_service.py   # PDF document downloading
├── managers/              # Resource management
│   └── token_manager.py      # Token rotation & captcha buffering
├── processors/            # Data processing
│   └── case_processor.py     # Case & document processing
├── repositories/          # Data persistence
│   └── case_repository.py    # MongoDB operations
├── configuration.py       # Configuration management
├── orchestrator.py        # Main orchestration logic
└── main.py               # Application entry point
```

## Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
```

Edit `.env` and set your credentials:
```env
CAPSOLVER_API_KEY=your_capsolver_api_key_here
PROXY_URL=http://username:password@proxy.com:port
```

3. **Start MongoDB**
Ensure MongoDB is running on `localhost:55000` or update `MONGODB_URI` in `.env`

4. **Prepare Case IDs**
Add case IDs to `case_ids.csv` (one per line)

## Usage

```bash
python main.py
```

## Configuration

All settings can be configured via environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `CAPSOLVER_API_KEY` | - | CapSolver API key (required) |
| `PROXY_URL` | - | Proxy URL for case requests |
| `USE_PROXY` | `true` | Enable/disable proxy usage |
| `CASE_WORKERS` | `3` | Concurrent case processing workers |
| `DOCUMENT_WORKERS` | `5` | Concurrent document downloads per case |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed requests |
| `TOKEN_REFRESH_INTERVAL` | `600` | Token refresh interval (seconds) |
| `CAPTCHA_BUFFER_SIZE` | `2` | Number of pre-solved captchas to maintain |
| `REQUEST_TIMEOUT` | `60` | HTTP request timeout (seconds) |
| `MONGODB_URI` | `mongodb://localhost:55000` | MongoDB connection URI |
| `MONGODB_DATABASE` | `scscourt` | MongoDB database name |
| `MONGODB_COLLECTION` | `cases` | MongoDB collection name |

## Data Structure

Each case is stored in MongoDB with the following structure:

```json
{
  "data": {
    "caseNumber": "24CV428648",
    "caseParties": [...],
    "caseEvents": [
      {
        "eventId": "121518060",
        "documents": [
          {
            "documentId": "CTht8Cx139r...",
            "documentName": "Minutes Non-Criminal",
            "pdf_base64": "JVBERi0xLjQK..."
          }
        ]
      }
    ],
    "caseHearings": [...],
    ...
  },
  "result": 0,
  "message": "Case number 5199169 was found"
}
```

## Logging

- Console output with colored status indicators
- Detailed logs saved to `scraper.log`
- Summary statistics at completion

## Notes

- Captcha solving may take 10-40 seconds per solution
- Token rotation happens automatically every 10 minutes
- Proxy is used only for case data requests, not for document downloads
- Duplicate cases (by case number) are automatically skipped
- Failed cases are retried up to `MAX_RETRIES` times before being marked as failed
