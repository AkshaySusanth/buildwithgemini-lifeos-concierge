import asyncio
import os
import time
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch Chromium headless
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        # Create context with video recording enabled
        recording_dir = "/config/Desktop/Session1/lifeos-concierge/recordings"
        os.makedirs(recording_dir, exist_ok=True)
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=recording_dir,
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        print("Navigating to http://localhost:8080 ...")
        await page.goto("http://localhost:8080", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # --- First Prompt: Core Subscription Math ---
        prompt1 = "Calculate my monthly subscription costs: Netflix $15.99/mo, Spotify $10.99/mo, Gym $49.99/mo."
        print(f"Typing Prompt 1: {prompt1}")
        input_el = page.locator("#input")
        await input_el.focus()
        
        for char in prompt1:
            await input_el.type(char, delay=40)
        await asyncio.sleep(0.5)
        
        print("Submitting Prompt 1...")
        await page.click("button")
        
        # Wait for agent reply bubble
        await page.wait_for_selector(".msg.agent:nth-child(2)", timeout=30000)
        # Wait until text finishes streaming (no longer shows '…')
        for _ in range(30):
            content = await page.text_content("#log")
            if "…" not in content:
                break
            await asyncio.sleep(1)
            
        print("Received reply for Prompt 1!")
        await asyncio.sleep(4)  # Pause to highlight result
        
        # --- Second Prompt: Richer Tool Call / Image Gen / Database / Holidays ---
        prompt2 = "What are the upcoming public holidays in the US for 2026? Also generate a cozy workspace image."
        print(f"Typing Prompt 2: {prompt2}")
        for char in prompt2:
            await input_el.type(char, delay=35)
        await asyncio.sleep(0.5)
        
        print("Submitting Prompt 2...")
        await page.click("button")
        
        # Wait for agent second reply bubble
        await page.wait_for_selector(".msg.agent:nth-child(4)", timeout=45000)
        for _ in range(45):
            content = await page.text_content("#log")
            # Wait for content to settle
            if content and not content.endswith("…"):
                break
            await asyncio.sleep(1)
            
        print("Received reply for Prompt 2!")
        await asyncio.sleep(6)  # Pause to showcase rich UI output & images
        
        video_path = await page.video.path()
        print(f"Recorded video saved to: {video_path}")
        
        await page.close()
        await context.close()
        await browser.close()
        return video_path

if __name__ == "__main__":
    asyncio.run(run())
