"""Web scraper for marathonguide.com to extract race results and event information."""
import csv
import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.marathonguide.com/results/search.cfm"


def sanitize_filename(name):
    """Convert a string into a valid filename by replacing non-alphanumeric chars with underscores."""
    # Replace non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')


def scrape_event_links(page):
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=True)
    #     page = browser.new_page()

    #     # Set a user agent
    #     page.set_extra_http_headers({
    #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    #     })

    try:
        # Increase timeout to 60 seconds and add error handling
        page.goto(BASE_URL, timeout=60000)
    except Exception as e:
        print(f"Error accessing {BASE_URL}: {str(e)}")
        # browser.close()
        return []

    # Initialize counter outside the loop
    # cnt = 0
    while True:
        try:
            load_more = page.locator("text=LOAD MORE")
            if load_more.is_visible():
                load_more.click()
                # cnt = cnt + 1
                time.sleep(3)  # wait for content to load
            else:
                break
        except:
            break

    # Extract event links
    event_elements = page.locator(".MuiBox-root .css-11pbu0q")
    event_count = event_elements.count()
    print(f"Found {event_count} events")

    events = []
    for i in range(event_count):
        el = event_elements.nth(i)
        href = el.locator("a").get_attribute("href")
        title = el.locator(".title").inner_text()
        info = el.locator(".information").inner_text()
        if href and "browse.cfm?MIDD=" in href:
            events.append((title.strip(), info.strip(),
                          f"https://www.marathonguide.com{href}"))

    return events


def get_race_results(page, event_url):
    try:
        page.goto(event_url, timeout=60000)

        # Wait for the results table to load
        # table = page.locator("table")
        # table.wait_for()
        while True:
            try:
                load_more = page.locator("text=LOAD MORE")
                if load_more.is_visible():
                    load_more.click()
                    time.sleep(3)  # wait for content to load
                else:
                    break
            except:
                break
        rows = []
        # Get all rows except header
        row_elements = page.locator("table tr")
        row_count = row_elements.count()

        for i in range(row_count):
            row = row_elements.nth(i)
            cols = row.locator(".MuiTableCell-root")
            col_texts = []
            col_count = cols.count()

            if col_count >= 5:  # Ensure we have enough columns
                for j in range(col_count):
                    col_texts.append(cols.nth(j).inner_text().strip())
                rows.append(col_texts)

        return rows
    except Exception as e:
        print(f"Error scraping results from {event_url}: {str(e)}")
        return []


def save_events_to_csv(events, filename="marathon_events.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Event Name", "Information", "URL"])
        writer.writerows(events)


if __name__ == "__main__":
    # events = scrape_event_links()
    # save_events_to_csv(events)
    # print(f"Saved {len(events)} events to marathon_events.csv")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Set user agent
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })

        # Get all events first
        events = scrape_event_links(page)

        # Now scrape results for each event

        # writer.writerow(["Place", "Full Name", "BIB", "Chip time", "Final Time", "Gender", "Location"])

        # For testing, limit to first 10 events
        for event_name, event_info, event_url in events:
            print(f"Scraping {event_name}")
            safe_name = sanitize_filename(event_name)
            output_file = f"output/{safe_name}.csv"
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                # Add event information as header rows
                writer.writerow(["Event Name:", event_name])
                writer.writerow(["Event Information:", event_info])
                writer.writerow([])  # Empty row for separation
                writer.writerow(["Race Results:"])
                try:
                    results = get_race_results(page, event_url)
                    for row in results:
                        writer.writerow(row)
                    time.sleep(1)  # polite delay
                except Exception as e:
                    print(f"Error with {event_url}: {e}")

        browser.close()
