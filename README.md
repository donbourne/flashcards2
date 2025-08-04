# Flashcards2: Music Flashcard Quiz App

## Overview

Flashcards2 is a Python-based flashcard quiz app focused on music recognition. Users are challenged to identify songs and artists from audio clips, with questions sourced manually or via YouTube searches. The app tracks user progress and adapts question difficulty based on performance.

## Features

- Add questions manually or by searching YouTube for official music videos.
- Clean and normalize artist and song names for consistency.
- Optionally filter YouTube results to only include popular videos.
- Adaptive quiz gameplay: questions are sorted and repeated based on your streaks.
- Progress tracking per user, with streak summaries after each question.
- Audio playback via YouTube links.

## Setup

1. **Clone the repository and set up your environment:**
    ```sh
    mkdir ~/PythonProjects/flashcards2
    cd ~/PythonProjects/flashcards2
    pyenv local 3.11.1
    python3 -m venv ~/PythonProjects/flashcards2/.venv
    source ~/PythonProjects/flashcards2/.venv/bin/activate
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3. **Set up your YouTube API key:**
    - Get an API key from [Google Developers Console](https://console.developers.google.com/).
    - Add it to your environment or `.env` file as `YOUTUBE_API_KEY`.

## Running
Run the app using the following commands:
```sh
cd ~/PythonProjects/flashcards2
source ~/PythonProjects/flashcards2/.venv/bin/activate
python3 flashcards.py
```

## Usage

- **Add Questions:**  
  Run the app and choose to add questions manually or via YouTube search.
- **Play Game:**  
  Start the quiz, answer questions, and track your progress.
- **Progress:**  
  After each question, see a summary of your streaks and completed questions.

## File Structure

- `flashcards.py` — Main app logic and game loop.
- `get_youtube_videos.py` — YouTube search and name cleaning utilities.
- `music_qa.csv` — Question database (auto-generated).
- `requirements.txt` — Python dependencies.
