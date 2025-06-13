import asyncio
import httpx
from youtube_caption_scraper import get_youtube_caption_url
import xml.etree.ElementTree as ET

def parse_subtitle_content(subtitle_content):
    try:
        root = ET.fromstring(subtitle_content)
        transcript = []
        for elem in root.findall('text'):
            start = float(elem.attrib['start'])
            dur = float(elem.attrib.get('dur', 0))
            text = elem.text or ''
            transcript.append({
                'start': start,
                'duration': dur,
                'text': text.replace('\n', ' ')
            })
        return transcript
    except Exception as e:
        print(f"Error parsing subtitle content: {e}")
        return []
    

async def fetch_transcript(video_id):
    try:
        # get_youtube_caption_url is an async function, so we await it
        caption_url = await get_youtube_caption_url(video_id)
        if not caption_url:
            print(f"No caption URL found for video ID: {video_id}. Captions might not be available.")
            return []
    except asyncio.TimeoutError:
        print(f"Timeout while trying to get caption URL for video ID: {video_id}.")
        return []
    except Exception as e:
        print(f"An error occurred while getting caption URL for {video_id}: {e}")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            # IMPORTANT: Use headers that mimic a browser, especially the Referer,
            # as YouTube can still block direct server-side access to caption URLs.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", # Or a generic browser UA
                "Accept": "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                # "Accept-Language": "en-US,en;q=0.9",
                # The Referer should point to your embed viewer page, as if the request originated from there.
                "Referer": f"http://127.0.0.1:8000/embed-viewer?video_id={video_id}", # Adjust this for your production URL
            }
            
            print(f"Attempting to fetch transcript content from URL: {caption_url}")
            response = await client.get(caption_url, headers=headers, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            subtitle_content = response.text
            
            # --- Parsing Mechanism (kept from your original code, adapted for XML) ---
            # Assuming 'srv1' gives XML, we use ET.fromstring for parsing
            return parse_subtitle_content(subtitle_content)

    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching caption content from {caption_url}: {e.response.status_code} - {e.response.text}")
        return []
    except httpx.RequestError as e:
        print(f"Network error fetching caption content from {caption_url}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during transcript content processing: {e}")
        return []