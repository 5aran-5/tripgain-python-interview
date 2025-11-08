# flight_search_automation_q3_q4.py
import asyncio
import json
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# --- Helper functions (same as before) ---
async def type_and_select(page, selector, city_name):
    """Helper to type city slowly and select from dropdown"""
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

async def pick_future_date(page):
    """Clicks any valid date within next 10 days on calendar"""
    print("Selecting journey date...")
    await page.click("label.datepicker.search-date", timeout=5000)
    await page.wait_for_selector(".ui-datepicker", timeout=5000)
    await page.wait_for_timeout(1500)

    from datetime import datetime as _dt
    today = _dt.utcnow().day
    future_days = [str((today + i) % 31 or 1) for i in range(1, 11)]

    for day in future_days:
        try:
            xpath = f"//td[contains(@class,'emp_Cells')]/span[text()='{day}']"
            await page.click(xpath, timeout=1000)
            print(f"✅ Picked date: {day}")
            return
        except:
            continue

    print("⚠️ Could not auto-pick a future date. Please click manually.")

def clean_price_to_int(price_text: str) -> int:
    """Convert string like '₹ 6,273.00' → 6273 (integer)"""
    if not price_text:
        return 0
    cleaned = re.sub(r"[^\d]", "", price_text)
    try:
        return int(cleaned)
    except ValueError:
        return 0

async def get_text_from_card(card, selectors):
    """Try multiple selectors and return first valid text"""
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
    """Extract visible flight data from all flight cards"""
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
                "price": price_int,
                "origin": origin,
                "destination": destination,
                "searchdatetime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            })
        except Exception as e:
            print(f"⚠️ Error extracting card #{idx}: {e}")
            continue

    return results

# --- main run function ---
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        context = await browser.new_context()
        page = await context.new_page()

        print("Opening BudgetTicket.in ...")
        await page.goto("https://www.budgetticket.in", timeout=60000)

        try:
            await page.click("text=Flights", timeout=5000)
        except:
            pass

        await page.wait_for_selector("input[placeholder='Select Origin City']", timeout=60000)

        # ✅ Q3 fields
        origin = "Bangalore"
        destination = "Delhi"

        print("Typing Origin city slowly...")
        await type_and_select(page, "input[placeholder='Select Origin City']", origin)

        print("Typing Destination city slowly...")
        await type_and_select(page, "input[placeholder='Select Destination City']", destination)

        await pick_future_date(page)

        print("Clicking Search Flights...")
        await page.click("input[type='submit'][value='Search']", timeout=10000)

        print("Waiting for flight results to appear...")
        await page.wait_for_selector("div.search-card.card", timeout=90000)
        await page.wait_for_timeout(3000)

        print("Extracting flights from page...")
        flights = await extract_flights_from_page(page, origin, destination)

        # ✅ Q4: Save + print total count
        out_filename = "flight_results.json"
        with open(out_filename, "w", encoding="utf-8") as f:
            json.dump(flights, f, indent=4, ensure_ascii=False)

        print(f"\n✅ Total Flights Extracted: {len(flights)}")
        print(f"💾 Results saved to: {out_filename}\n")

        # show first few results
        for i, fl in enumerate(flights[:5], 1):
            print(f"{i}. {fl['airline']} | {fl['flight_number']} | {fl['departure']} -> {fl['arrival']} | ₹{fl['price']}")

        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
