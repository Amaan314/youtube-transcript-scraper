import asyncio
from playwright.async_api import async_playwright, Request
import logging
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_youtube_caption_url(video_id: str) -> str | None:
    """
    Launches a headless browser, navigates to an embedded YouTube video on our FastAPI server,
    captures the first 'fmt=json3' timedtext URL, modifies it to 'fmt=srv1', and returns the new URL.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch() # You can add headless=False for debugging UI
        page = await browser.new_page()

        captured_modified_caption_url = None
        caption_url_found_event = asyncio.Event()

        def is_relevant_caption_request(request_url: str) -> bool:
            """
            Checks if a given URL is a YouTube timedtext request for the target video ID,
            and contains 'fmt=' (typically 'fmt=json3' as per your observation).
            """
            parsed_url = urlparse(request_url)
            is_youtube_domain = any(
                domain in parsed_url.netloc for domain in ["youtube.com", "googleusercontent.com", "googlevideo.com"]
            )
            is_timedtext_path = "/api/timedtext" == parsed_url.path

            if is_youtube_domain and is_timedtext_path:
                query_params = parse_qs(parsed_url.query)
                # Ensure it's for the correct video and has an 'fmt' parameter
                if query_params.get('v') == [video_id] and 'fmt' in query_params:
                    logger.debug(f"Relevant caption request URL identified: {request_url}")
                    return True
            return False

        async def handle_request(request: Request):
            nonlocal captured_modified_caption_url

            # If we've already found and modified the URL, no need to process further requests
            if captured_modified_caption_url:
                return

            if is_relevant_caption_request(request.url):
                # We are confident it's a 'fmt=json3' URL as per your testing
                if "fmt=json3" in request.url:
                    # Replace 'fmt=json3' with 'fmt=srv1'
                    modified_url = request.url.replace("fmt=json3", "fmt=srv1")
                    captured_modified_caption_url = modified_url
                    logger.info(f"Original fmt=json3 URL captured: {request.url}")
                    logger.info(f"Modified URL to fmt=srv1: {captured_modified_caption_url}")
                    caption_url_found_event.set() # Signal that we have the URL

        # Register the request handler
        page.on("request", handle_request)

        try:
            # Construct the URL to your FastAPI's embed viewer endpoint
            embed_viewer_url = f"https://youtube-transcript-scraper-production.up.railway.app/embed-viewer?video_id={video_id}"
            # embed_viewer_url = f"https://amaanp314-youtube-ai-analyzer.hf.space/embed-viewer?video_id={video_id}"
            logger.info(f"Navigating headless browser to: {embed_viewer_url}")

            # Navigate to the page and wait for it to be fully loaded
            await page.goto(embed_viewer_url, wait_until="networkidle")

            # Wait for the event to be set, indicating a modified caption URL has been captured.
            # Increase timeout slightly to allow player to fully load and make requests.
            await asyncio.wait_for(caption_url_found_event.wait(), timeout=10) 

            if captured_modified_caption_url:
                logger.info(f"Successfully returned modified caption URL for {video_id}: {captured_modified_caption_url}")
                return captured_modified_caption_url
            else:
                logger.warning(f"No relevant caption URL intercepted for {video_id} within the timeout. This might indicate no captions are available or a problem with the embed/detection.")
                return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for a caption URL for video ID: {video_id}.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Playwright operation for {video_id}: {e}")
            return None
        finally:
            await browser.close()
            logger.info("Headless browser closed.")
