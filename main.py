from fastapi import FastAPI
from transcript import fetch_transcript
import uvicorn
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/embed-viewer", response_class=HTMLResponse)
async def embed_viewer(video_id: str):
    """
    Serves a minimal HTML page containing a YouTube video embed.
    This page is visited by the headless browser to trigger caption loading and toggling.
    """
    embed_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube Embed Viewer</title>
        <style>
            body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #000; }}
            #player {{ width: 100vw; height: 100vh; }}
        </style>
    </head>
    <body>
        <div id="player"></div>
        <script>
            var tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

            var player;
            function onYouTubeIframeAPIReady() {{
                player = new YT.Player('player', {{
                    videoId: '{video_id}',
                    playerVars: {{
                        'controls': 1,
                        'autoplay': 1,
                        'mute': 1,
                        'cc_load_policy': 1,   // Start with captions ON
                        'enablejsapi': 1,
                        'modestbranding': 1,
                        'rel': 0,
                        'showinfo': 0
                    }},
                    events: {{
                        'onReady': onPlayerReady,
                        'onStateChange': onPlayerStateChange
                    }}
                }});
            }}

            function onPlayerReady(event) {{
                console.log('Player ready. Toggling captions off then on...');
                // Turn captions OFF programmatically
                player.setOption('captions', 'track', {{}});
                // Then after a short delay, turn them back ON in English
                setTimeout(function() {{
                    player.setOption('captions', 'track', {{ languageCode: 'en' }});
                }}, 1000);
            }}

            function onPlayerStateChange(event) {{
                // Optional debugging
                // console.log('Player state changed:', event.data);
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=embed_html)

# @app.get("/embed-viewer", response_class=HTMLResponse)
# async def embed_viewer(video_id: str):
#     """
#     Serves a minimal HTML page containing a YouTube video embed.
#     This page is visited by the headless browser to trigger caption loading.
#     """
#     embed_html = f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>YouTube Embed Viewer</title>
#         <style>
#             body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #000; }}
#             #player {{ width: 100vw; height: 100vh; }}
#         </style>
#     </head>
#     <body>
#         <div id="player"></div>
#         <script>
#             var tag = document.createElement('script');
#             tag.src = "https://www.youtube.com/iframe_api"; // Official YouTube IFrame Player API
#             var firstScriptTag = document.getElementsByTagName('script')[0];
#             firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

#             var player;
#             function onYouTubeIframeAPIReady() {{
#                 player = new YT.Player('player', {{
#                     videoId: '{video_id}',
#                     playerVars: {{
#                         'controls': 1,
#                         'autoplay': 1,
#                         'mute': 1, // Mute for autoplay (required by modern browsers)
#                         'cc_load_policy': 1, // Crucially, enable captions automatically
#                         'enablejsapi': 1,
#                         'modestbranding': 1,
#                         'rel': 0, // Don't show related videos
#                         'showinfo': 0 // Don't show video title/uploader info
#                     }},
#                     events: {{
#                         'onReady': onPlayerReady,
#                         'onStateChange': onPlayerStateChange
#                     }}
#                 }});
#             }}

#             function onPlayerReady(event) {{
#                 // Player is ready, captions should be attempting to load internally
#                 console.log('Player ready and trying to load captions.');
#             }}

#             function onPlayerStateChange(event) {{
#                 // Optional: You can log player state changes if debugging
#                 // console.log('Player state changed:', event.data);
#             }}
#         </script>
#     </body>
#     </html>
#     """
#     return HTMLResponse(content=embed_html)

@app.get(
    "/video/transcript/{video_id}",
    summary="Get Video Transcript",
    description="Fetches the transcript of a YouTube video with timestamps.",
    tags=["Video"]
)   
async def get_video_transcript(video_id: str):
    """Get the full transcript of a YouTube video."""
    try:
        transcript = await fetch_transcript(video_id)
        if not transcript:
            print(f"No transcript found or an issue occurred for video ID: {video_id}")
            return []
        return transcript
    except Exception as e:
        print(f"Error fetching transcript for video ID {video_id}: {e}")
        return []
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
