# California Court Scraper

Advanced web scraping system for California court public data with automatic token rotation, concurrent processing, and Supabase storage.

## Features

- **SOLID Architecture**: Clean separation of concerns with services, managers, processors, and repositories
- **Automatic Token Rotation**: Refreshes authentication tokens every 10 minutes
- **Captcha Buffer System**: Maintains 2 pre-solved captchas to avoid scraping interruptions
- **Concurrent Processing**: Processes 3 cases simultaneously, each downloading 5 documents in parallel
- **Retry Mechanism**: Automatic retry with configurable attempts for failed requests
- **Supabase Storage**: Stores case data in 5 normalized tables with PDF documents in cloud storage
- **Colored Logging**: Clear, informative console output with progress tracking
- **Proxy Support**: Optional proxy configuration for case data requests

## Architecture

```
├── logger.py          # Colored logging utility
├── services.py        # API services (Captcha, Token, Case, Document)
├── core.py            # TokenManager & CaseProcessor
├── database.py        # Supabase repository with 5 tables
├── scraper.py         # Main scraper orchestrator
├── configuration.py   # Configuration management
└── main.py            # Application entry point
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

3. **Setup Supabase Database**
Run the SQL schema in your Supabase SQL editor:
```bash
cat supabase_schema.sql
```
This creates 5 tables: cases, parties, attorneys, hearings, documents

Also create a storage bucket named "documents" in Supabase Storage

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
| `SUPABASE_URL` | - | Supabase project URL (required) |
| `SUPABASE_KEY` | - | Supabase API key (required) |
| `CASE_WORKERS` | `3` | Concurrent case processing workers |
| `DOCUMENT_WORKERS` | `5` | Concurrent document downloads per case |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed requests |
| `TOKEN_REFRESH_INTERVAL` | `600` | Token refresh interval (seconds) |
| `CAPTCHA_BUFFER_SIZE` | `2` | Number of pre-solved captchas to maintain |
| `REQUEST_TIMEOUT` | `60` | HTTP request timeout (seconds) |

## Data Structure

Data is stored in 5 normalized Supabase tables:

### 1. **cases** table
- case_number (PK), type, style, file_date, status, court_location

### 2. **parties** table
- case_number (FK), type, first_name, middle_name, last_name, nick_name, business_name, full_name, is_defendant

### 3. **attorneys** table
- case_number (FK), first_name, middle_name, last_name, representing, bar_number, is_lead

### 4. **hearings** table
- case_number (FK), hearing_id, calendar, type, date, time, hearing_result

### 5. **documents** table
- case_number (FK), document_name

### PDF Storage
PDFs are stored in Supabase Storage bucket "documents" organized by case_number:
```
documents/
  ├── 24CV428648/
  │   ├── Minutes-Non-Criminal.pdf
  │   ├── Request-for-Dismissal.pdf
  │   └── ...
  └── 22CH010501/
      └── ...
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
- Document names are cleaned (special chars removed, spaces replaced with hyphens)
- PDFs are automatically uploaded to Supabase Storage organized by case_number folders
