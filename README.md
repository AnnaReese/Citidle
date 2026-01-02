# Citidle 

A daily geography guessing game where you try to identify a mystery US city. Inspired by [Globle](https://globle-game.com/) and [Wordle](https://www.nytimes.com/games/wordle).

## A Note From the Author:
I made this game because I absolutely love Globle and play it everyday.
From Globle I have signifigantly improved my geography skills and country knowledge. 
I recently realized that I still have a gap in my geography skills though: US cities.
This inspired me to create this project for myself and others so we can all look smart when we know where Henderson and Stockton are on a map!
<br>
Additionally, this project is my first expirement coding with AI. 
I generally have stayed away from coding with AI to make sure that I build my own skills.
However, I know that it is a powerful tool that I need to be able to harness.
I started developing this using GPT-5 mini and eventually got the GitHub student subscription to Claude Opus 4.5 which is AMAZING at coding, troubleshooting, and taking my feedback + putting it to action. 
Despite using AI, I still found myself having a hands on role in the development of Citidle. 
Particuarly, giving feedback on UI and functionality, directing it through very detailed prompts, and making development descions like how to host Citidle.
<br>
I hope you enjoy playing!

## How to Play

1. **Guess a US city** with a population of 300,000 or more
2. **See your guess on the map** — the color indicates how close you are:
   - 🟢 **Green** — Very close (under 100 miles)
   - 🟡 **Yellow** — Getting warmer (100-500 miles)
   - 🟠 **Orange** — Getting there (500-1000 miles)
   - 🔴 **Red** — Far away (1000+ miles)
3. **Keep guessing** until you find the target city
4. **New city every day** — resets at midnight CST

## Features

- Interactive US map with Leaflet.js
- Visual feedback showing all your guesses
- Distance and direction hints for each guess
- Progress saved locally — come back anytime
- New puzzle daily at midnight Central Time

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript, Leaflet.js
- **Data:** US cities with 300k+ population (CSV)
- **Deployment:** Railway with Gunicorn

## Project Structure

```
├── web.py              # Flask API server
├── game/
│   ├── daily.py        # Daily city selection (CST timezone)
│   ├── distance.py     # Haversine distance calculations
│   └── engine.py       # Game state and logic
├── static/
│   └── index.html      # Web UI
├── data/
│   └── cities.csv      # City database
└── tests/              # Pytest test suite
```

## How It Works

### Daily City Selection
Each day's target city is deterministically selected using a SHA-256 hash of the current CST date. This ensures:
- Everyone plays the same city each day
- The sequence is unpredictable but reproducible

### Distance Calculation
Uses the [Haversine formula](https://en.wikipedia.org/wiki/Haversine_formula) to calculate great-circle distances between coordinates, giving accurate distances in miles.

### City Matching
Supports flexible input with:
- Case-insensitive matching
- Common aliases (e.g., "NYC" → "New York")
- State disambiguation (e.g., "Portland, OR" vs "Portland, ME")

## Development

### Setup

```bash
# Clone the repo
git clone https://github.com/AnnaReese/Citidle.git
cd Citidle

# Install dependencies
pip install -r requirements.txt

# Run locally
python web.py
```

### Testing

```bash
python -m pytest tests/ -v
```

### Deployment

Configured for Railway deployment with `Procfile` and `gunicorn`.

## License

MIT

