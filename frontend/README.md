# Fraud Detection Frontend

A React + Vite frontend for the Flask fraud detection API in this repository.

## Features

- Check API health (`/api/health`)
- Submit transaction details (amount, time, transaction type, location) to get a fraud prediction
- Shows prediction result and fraud probability when available

## Setup

1. Install dependencies

```bash
npm install
```

2. Configure API base URL

Copy `.env.example` to `.env` and update if your backend runs on a different host/port:

```bash
cp .env.example .env
```

3. Start the dev server

```bash
npm run dev
```

The app will be available at `http://localhost:5173` by default.

## Backend

Make sure the Flask backend (`app.py`) is running on `http://127.0.0.1:5000` (or update `VITE_API_BASE_URL`). The backend expects CORS allowed origins to include `http://localhost:5173` (already configured via `FRONTEND_ORIGINS` env var).

## Build

```bash
npm run build
```

The production build will be output to `dist/`.
