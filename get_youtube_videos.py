import googleapiclient.discovery
import re
import unicodedata

def clean_name(name):
    original_name = name

    # Remove anything in round or square brackets
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    
    # Remove emojis
    name = ''.join(c for c in name if unicodedata.category(c) != 'So')
    
    # Replace special characters with the closest non-special character
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    
    # Remove any references to M/V or MV
    name = re.sub(r'\bMV\b', '', name)
    name = re.sub(r'\bM/V\b', '', name)

    # Remove any single or double quotes
    name = name.replace("'", "").replace('"', "")

    # Replace any &#39; with an apostrophe
    name = name.replace("&#39;", "'")

    # Replace any &amp; with an ampersand
    name = name.replace("&amp;", "&")

    # Replace ", " with " & "
    name = name.replace(", ", " & ")

    # Remove single quotes at the beginning or end of the string
    name = re.sub(r"(^\'|\'$)", '', name)

    # Remove single quotes preceded or followed by a space
    name = re.sub(r"\s\'|\'\s", ' ', name)

    # Remove any multiple spaces
    name = re.sub(r'\s+', ' ', name)

    # Remove any leading or trailing whitespace
    name = name.strip()

    if name != original_name:
        print(f"Cleaned '{original_name}' to '{name}'") 

    return name

def get_youtube_videos(api_key, query, max_results=10, only_include_popular=False, view_threshold=1000000):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    videos = []
    for item in response['items']:
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        url = f"https://www.youtube.com/watch?v={video_id}"
        artist, song = title.split(" - ", 1) if " - " in title else (title, "")
        if not artist or not song:
            print(f"Skipping {title} (could not extract artist and song)")
            continue
                
        # Clean artist and song names
        artist = clean_name(artist)
        song = clean_name(song)
        if not artist or not song:
            print(f"Skipping {title} (nothing left after cleaning artist and song)")
            continue

        if only_include_popular:
            # Get video statistics
            stats_request = youtube.videos().list(
                part="statistics",
                id=video_id
            )
            stats_response = stats_request.execute()
            view_count = int(stats_response['items'][0]['statistics']['viewCount'])
            if view_count < view_threshold:
                print(f"Skipping {artist} - {song} (view count: {view_count})")
                continue
        
        videos.append((url, artist, song))
    return videos