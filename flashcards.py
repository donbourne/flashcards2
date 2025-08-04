import os
import csv
import json
import random
import re
import webbrowser
import subprocess
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv 
from get_youtube_videos import get_youtube_videos

class Question:
    def __init__(self, question):
        self.question = question

    def play_audio(self, offset=None):
        if offset:
            url_parts = list(urlparse(self.question))
            query = parse_qs(url_parts[4])
            query['t'] = offset
            url_parts[4] = urlencode(query, doseq=True)
            url_with_offset = urlunparse(url_parts)
            webbrowser.open(url_with_offset)
        else:
            webbrowser.open(self.question)

    def __repr__(self):
        return f"Question(question={self.question})"

class Answer:
    def __init__(self, correct_answer):
        self.correct_answer = tuple(correct_answer)  # Ensure correct_answer is stored as a tuple

    def clean_string(self, s):
        # Remove "ft."
        s = s.replace('ft.', '')
        s = s.replace('feat.', '')

        # Remove punctuation and ampersands, and convert to lowercase
        s = re.sub(r'[^\w\s]', '', s)  # Remove punctuation
        s = s.replace('& ', '')  # Remove ampersands

        # replace multiple spaces with a single space
        s = re.sub(r'\s+', ' ', s)

        return s.lower().strip()

    def check_answer(self, given_answer) -> bool:
        # Clean the correct and given answers
        correct = tuple(self.clean_string(part) for part in self.correct_answer)
        given = tuple(self.clean_string(part) for part in given_answer)

        # Check if all parts of the given answer are 'y'
        if all(part == 'y' for part in given):
            return True

        print(f"XXX Correct answer: {correct}")
        print(f"XXX Given answer: {given}")

        return correct == given
    
    def __repr__(self):
        return f"Answer(correct_answer={self.correct_answer})"

class QuestionAnswerPair:
    def __init__(self, id: int, question: Question, answer: Answer):
        self.id = id
        self.question = question
        self.answer = answer

    def __repr__(self):
        return f"QuestionAnswerPair(id={self.id}, question={self.question}, answer={self.answer})"

class KnowledgeBase:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.pairs = []

    def add_pair(self, pair: QuestionAnswerPair):
        self.pairs.append(pair)

    def __repr__(self):
        return f"KnowledgeBase(id={self.id}, name={self.name}, pairs={self.pairs})"

class User:
    def __init__(self, id: int, username: str):
        self.id = id
        self.username = username

    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"
    
class UserKnowledge:
    def __init__(self, id: int, user_id: int, knowledge_id: int, level: int):
        self.id = id
        self.user_id = user_id
        self.knowledge_id = knowledge_id
        self.level = level

    def __repr__(self):
        return f"UserKnowledge(id={self.id}, user_id={self.user_id}, knowledge_id={self.knowledge_id}, level={self.level})"

def load_csv(knowledge_base):
    knowledge_base.pairs.clear()
    if os.path.exists('music_qa.csv'):
        with open('music_qa.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['id'].startswith('#'):
                    continue
                question = Question(row['question'])
                answer = Answer((row['artist'], row['song']))
                pair = QuestionAnswerPair(int(row['id']), question, answer)
                knowledge_base.add_pair(pair)

def write_to_csv(knowledge_base, filename='music_qa.csv'):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['id', 'question', 'artist', 'song']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for pair in knowledge_base.pairs:
            writer.writerow({
                'id': pair.id,
                'question': pair.question.question,
                'artist': pair.answer.correct_answer[0],
                'song': pair.answer.correct_answer[1]
            })

def enter_song_questions(knowledge_base):
    pair_id = 1

    mode = input("Enter '1' to add questions manually or '2' to query YouTube videos: ")
    if mode == '1':
        # Load existing pairs if the file exists
        load_csv(knowledge_base)
        if knowledge_base.pairs:
            pair_id = max(pair.id for pair in knowledge_base.pairs) + 1
        while True:
            audio_url = input("Enter the URL for the audio question (or 'exit' to finish): ")
            if audio_url.lower() == 'exit':
                break

            question = Question(audio_url)

            artist_name = input("Enter the artist name: ")
            song_name = input("Enter the song name: ")
            answer = Answer((artist_name, song_name))

            pair = QuestionAnswerPair(id=pair_id, question=question, answer=answer)
            knowledge_base.add_pair(pair)
            pair_id += 1

        write_to_csv(knowledge_base)
    elif mode == '2':
        api_key = os.getenv("YOUTUBE_API_KEY")
        while True:
            query = input("Enter additional search query (e.g., artist name) or 'exit' to finish: ")
            if query.lower() == 'exit':
                break
            
            # Load existing pairs if the file exists
            load_csv(knowledge_base)
            if knowledge_base.pairs:
                pair_id = max(pair.id for pair in knowledge_base.pairs) + 1

            full_query = f"{query} official music video"
            try:
                videos = get_youtube_videos(api_key, full_query, max_results=10, only_include_popular=True, view_threshold=1000000)
                for url, artist, song in videos:
                    question = Question(url)
                    answer = Answer((artist, song))
                    pair = QuestionAnswerPair(id=pair_id, question=question, answer=answer)
                    knowledge_base.add_pair(pair)
                    pair_id += 1
                    print(f"Added: {artist} - {song}")

                # Update the CSV file after each search
                write_to_csv(knowledge_base)
            except Exception as e:
                print(f"Error querying YouTube: {e}")


def close_browser_tab():
    script = """
    tell application "Google Chrome"
        close tab 1 of window 1
    end tell
    """
    subprocess.run(["osascript", "-e", script])

def play_game(knowledge_base):
    username = input("Enter your username: ")
    user_file = f"user_{username}.json"
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            user_stats = json.load(f)
    else:
        user_stats = {"username": username, "knowledge": {}}

    def get_correct_streak(pair_id):
        return user_stats["knowledge"].get(str(pair_id), 0)

    def update_correct_streak(pair_id, correct):
        if correct:
            user_stats["knowledge"][str(pair_id)] = get_correct_streak(pair_id) + 1
        else:
            user_stats["knowledge"][str(pair_id)] = 0

    def generate_ordered_pairs():
        pairs = knowledge_base.pairs
        streaks = {}
        for pair in pairs:
            streak = get_correct_streak(pair.id)
            if streak not in streaks:
                streaks[streak] = []
            streaks[streak].append(pair)

        ordered_pairs = []
        for streak in sorted(streaks.keys()):
            if streak == 0:
                streaks[streak].sort(key=lambda pair: pair.answer.correct_answer[0])  # Sort by artist for streak == 0
            else:
                random.shuffle(streaks[streak])
            ordered_pairs.extend(streaks[streak])

        # print the full list of ordered pairs
        for pair in ordered_pairs:
            print(f"{pair.id}: {pair.answer.correct_answer[0]} - {pair.answer.correct_answer[1]}")

        return ordered_pairs

    def print_streak_summary():
        streak_distribution = {}
        for pair in knowledge_base.pairs:
            streak = get_correct_streak(pair.id)
            if streak not in streak_distribution:
                streak_distribution[streak] = 0
            streak_distribution[streak] += 1

        done_count = streak_distribution.pop(4, 0)  # Remove and get the count of completed questions
        summary = ", ".join(f"streak {streak}: {count}" for streak, count in sorted(streak_distribution.items()))
        print(f"Streak distribution: {summary}, done: {done_count}")

        # print a distribution summary using *s for each streak
        for streak, count in sorted(streak_distribution.items()):
            print(f"Streak {streak}: {'*' * count}")
    
    ordered_pairs = generate_ordered_pairs()
    last_modified_time = os.path.getmtime('music_qa.csv')

    while ordered_pairs:
        next_pair = ordered_pairs.pop(0)
        correct_streak = get_correct_streak(next_pair.id)
        
        if correct_streak == 0:
            print(f"{next_pair.answer.correct_answer[0]} - {next_pair.answer.correct_answer[1]}")

        if correct_streak >= 4:
            print(f"Skipping {next_pair.question.question} - already completed")
            continue

        if correct_streak > 2:
            url_parts = list(urlparse(next_pair.question.question))
            query = parse_qs(url_parts[4])
            start_offset = int(query.get('t', [0])[0])
            random_offset = random.randint(start_offset, start_offset + 120)
            next_pair.question.play_audio(offset=random_offset)
        else:
            next_pair.question.play_audio()
        
        artist_name = input("Enter the artist name: ")
        song_name = input("Enter the song name: ")
        correct = next_pair.answer.check_answer((artist_name, song_name))

        if correct:
            correct_streak = get_correct_streak(next_pair.id) + 1
            if correct_streak < 4:
                new_position = min(len(ordered_pairs), 2 ** (correct_streak + 1))
                ordered_pairs.insert(new_position, next_pair)
                print(f"Correct! The correct answer was {next_pair.answer.correct_answer[0]} - {next_pair.answer.correct_answer[1]}. - new position: {new_position}")
            else:
                print(f"Correct! The correct answer was {next_pair.answer.correct_answer[0]} - {next_pair.answer.correct_answer[1]}. - DONE!")
        else:
            ordered_pairs.insert(min(len(ordered_pairs), 2), next_pair)
            print(f"Incorrect! The correct answer was {next_pair.answer.correct_answer[0]} - {next_pair.answer.correct_answer[1]}. new position: {min(len(ordered_pairs), 2)}")
        update_correct_streak(next_pair.id, correct)

        # Close the browser tab
        close_browser_tab()

        if correct:
            # play a success sound
            os.system("afplay /System/Library/Sounds/Ping.aiff")
        else:
            # play a buzzer sound
            os.system("afplay /System/Library/Sounds/Basso.aiff")

        with open(user_file, 'w') as f:
            json.dump(user_stats, f, indent=4)

        # Print streak summary
        print_streak_summary()

        # Check if the CSV file has changed
        current_modified_time = os.path.getmtime('music_qa.csv')
        if current_modified_time != last_modified_time:
            load_csv(knowledge_base)
            ordered_pairs = generate_ordered_pairs()
            last_modified_time = current_modified_time
            print("Reloaded questions from the CSV file")

def append_to_csv(file_path, data):
    with open(file_path, 'a', newline='') as csvfile:
        fieldnames = ['id', 'question', 'artist', 'song']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for i, (url, artist, song) in enumerate(data, start=1):
            writer.writerow({
                'id': i,
                'question': url,
                'artist': artist,
                'song': song
            })

def main():
    load_dotenv()
    knowledge_base = KnowledgeBase(id=1, name="Music Knowledge Base")

    mode = input("Enter '1' to add song questions/answers or '2' to play the game: ")
    if mode == '1':
        enter_song_questions(knowledge_base)
    elif mode == '2':
        load_csv(knowledge_base)
        play_game(knowledge_base)

if __name__ == "__main__":
    main()