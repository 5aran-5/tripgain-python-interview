# ------------------------------------------------------------------
# ✅ FIX 1: Must set Windows event loop policy BEFORE any imports
# ------------------------------------------------------------------
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------
import re
from datetime import datetime, timezone
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------
async def type_and_select(page, selector, city_name):
    input_box = await page.query_selector(selector)
    await input_box.click()
    await page.fill(selector, "")
    for ch in city_name:
        await input_box.type(ch)
        await page.wait_for_timeout(10)
    await page.wait_for_timeout(100)
    await page.keyboard.press("ArrowDown")
    await page.wait_for_timeout(100)
    await page.keyboard.press("Enter")


def clean_price_to_int(price_text: str) -> int:
    if not price_text:
        return 0
    cleaned = re.sub(r"[^\d.]", "", price_text)
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


async def get_text_from_card(card, selectors):
    for sel in selectors:
        try:
            el = await card.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                if txt:
                    return txt
                attr = await el.get_attribute("alt") or await el.get_attribute("value")
                if attr:
                    return attr.strip()
        except:
            continue
    return "N/A"


async def extract_flights_from_page(page, origin, destination):
    await page.wait_for_timeout(2000)
    cards = await page.query_selector_all("div.search-card.card")
    results = []

    for idx, card in enumerate(cards):
        try:
            airline = await get_text_from_card(card, [
                "p.h6.responsive-bold", "div .text-left p.h6", "img.air-logo-md"
            ])
            flight_no = await get_text_from_card(card, [
                "p.mb-0.d-inline.d-lg-block", "div p.mb-0.d-inline"
            ])
            dep_time = await get_text_from_card(card, [
                "div.col-4.col-md-3.text-right span.text-mild-dark"
            ])
            arr_time = await get_text_from_card(card, [
                "div.col-4.col-md-3.text-left span.text-mild-dark"
            ])
            price_text = await get_text_from_card(card, [
                "p.text-gray.roboto_font", "p.lbl-huge",
                "p.text-gray.roboto_font.mb-0.text-primary",
                "div.col-12.col-md-12 p.font-weight-600"
            ])

            price_int = clean_price_to_int(price_text)

            results.append({
                "airline": airline.replace("\n", " ").strip() or "N/A",
                "flight_number": flight_no.replace("\n", " ").strip() or "N/A",
                "departure": dep_time.replace("\n", " ").strip() or "N/A",
                "arrival": arr_time.replace("\n", " ").strip() or "N/A",
                "price": float(price_int),  # ✅ make price float
                "origin": origin,
                "destination": destination,
                "searchdatetime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            })
        except Exception as e:
            print(f"⚠️ Error extracting card #{idx}: {e}")
            continue
    return results


async def search_flights(origin: str, destination: str, journey_date: str):
    """Runs Playwright automation"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.budgetticket.in", timeout=60000)
        await page.wait_for_selector("input[placeholder='Select Origin City']", timeout=60000)
        await type_and_select(page, "input[placeholder='Select Origin City']", origin)
        await type_and_select(page, "input[placeholder='Select Destination City']", destination)

        # Date selection
        await page.click("label.datepicker.search-date", timeout=5000)
        await page.wait_for_selector(".ui-datepicker", timeout=5000)
        await page.wait_for_timeout(1000)
        try:
            xpath = f"//td[contains(@class,'emp_Cells')]/span[text()='{journey_date}']"
            await page.click(xpath, timeout=3000)
        except:
            print(f"⚠️ Could not pick date {journey_date}")

        await page.click("input[type='submit'][value='Search']", timeout=10000)
        await page.wait_for_selector("div.search-card.card", timeout=90000)

        flights = await extract_flights_from_page(page, origin, destination)
        await browser.close()
        return flights


# ------------------------------------------------------------------
# ✅ FIX 2: Run Playwright safely in background thread
# ------------------------------------------------------------------
def run_scraper_in_thread(origin, destination, journey_date):
    return asyncio.run(search_flights(origin, destination, journey_date))


# ------------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------------
app = FastAPI(title="Flight Search API", version="2.0")


@app.get("/flight-search")
async def flight_search(
    origin: str = Query(...),
    destination: str = Query(...),
    journey_date: str = Query(...)
):
    try:
        # ✅ Safer way to isolate Playwright loop
        loop = asyncio.get_running_loop()
        flights = await loop.run_in_executor(None, run_scraper_in_thread, origin, destination, journey_date)
        if not flights:
            return JSONResponse({"message": "No flights found"}, status_code=404)
        return JSONResponse(content=flights, status_code=200)
    except Exception as e:
        print("❌ Error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)
