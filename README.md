# NBA Playoffs Display

A Flask application that fetches and displays NBA playoff game data, optimized for e-ink displays through TRMNL.

## Features

- NBA playoff game data
- Series records for each matchup
- Optimized display for e-ink screens
- Responsive design for different TRMNL layouts

## API Endpoints

- `/` - Health check endpoint
- `/recent-games` - Returns recent playoff games with series records

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file
   - Add your BallDontLie API key:
     ```
     BALLDONTLIE_API_KEY=your_api_key_here
     ```

## Development

Run the development server:
```bash
python nba_playoffs.py
```

## Production Deployment

The application is configured to run with Gunicorn in production. Railway will automatically use the Procfile to start the application.

## TRMNL Layouts

The application supports multiple TRMNL layouts:
- Full screen
- Half screen (vertical)
- Half screen (horizontal)
- Quarter screen

Each layout is optimized for the specific display size while maintaining readability and information hierarchy.
