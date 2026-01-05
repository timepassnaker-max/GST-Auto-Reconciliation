# GST Reconciliation Tool

A professional web application for GST reconciliation with a modern, beautiful UI.

## Features
- Upload Excel files with Portal and Books data
- Automatic reconciliation and matching
- Download reconciled results
- Download blank template for data entry
- Beautiful, responsive UI with glassmorphism design

## Deployment

This application is deployed on Render.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python -m uvicorn backend.main:app --reload
```

3. Open your browser to `http://localhost:8000`

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Data Processing**: Pandas, OpenPyXL
- **Deployment**: Render

## License
MIT
