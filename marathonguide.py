"""Web scraper for marathonguide.com to extract race results and event information."""
import csv
import re
import time
import os
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.marathonguide.com/results/search.cfm"
INDEX_FILE = "index.csv"
OUTPUT_DIR = "output"

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def load_index():
    """Load existing events from index.csv."""
    events = {}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events[row['url']] = {
                    'name': row['name'],
                    'info': row['info'],
                    'downloaded': row['downloaded'] == 'True',
                    'has_location': row['has_location'] == 'True'
                }
    return events

def save_to_index(events):
    """Save events to index.csv."""
    with open(INDEX_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'info', 'url', 'downloaded', 'has_location'])
        writer.writeheader()
        for url, data in events.items():
            writer.writerow({
                'name': data['name'],
                'info': data['info'],
                'url': url,
                'downloaded': str(data['downloaded']),
                'has_location': str(data['has_location'])
            })

def sanitize_filename(name):
    """Convert a string into a valid filename by replacing non-alphanumeric chars with underscores."""
    # Replace non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')


def scrape_event_links(page):

    try:
        # Increase timeout to 60 seconds and add error handling
        page.goto(BASE_URL, timeout=60000)
    except Exception as e:
        print(f"Error accessing {BASE_URL}: {str(e)}")
        return []

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

    # Extract event links
    event_elements = page.locator(".MuiBox-root .css-11pbu0q")
    event_count = event_elements.count()
    print(f"Found {event_count} events")
# https://www.marathonguide.com/results/browse.cfm?MIDD=68905250504&year=2025
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

        # Check if location column exists
        has_location = False
        if row_count > 0:
            header_row = row_elements.nth(0)
            header_cols = header_row.locator(".MuiTableCell-root")
            for i in range(header_cols.count()):
                if "Location" in header_cols.nth(i).inner_text():
                    has_location = True
                    break

        if not has_location:
            return [], False

        for i in range(1, row_count):  # Start from 1 to skip header
            row = row_elements.nth(i)
            cols = row.locator(".MuiTableCell-root")
            col_texts = []
            col_count = cols.count()

            if col_count >= 5:  # Ensure we have enough columns
                for j in range(col_count):
                    col_texts.append(cols.nth(j).inner_text().strip())
                rows.append(col_texts)

        return rows, True
    except Exception as e:
        print(f"Error scraping results from {event_url}: {str(e)}")
        return [], False


def save_events_to_csv(events, filename="marathon_events.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Event Name", "Information", "URL"])
        writer.writerows(events)


if __name__ == "__main__":
    ensure_output_dir()
    existing_events = load_index()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Set user agent
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })

        # Get all events first
        new_events = scrape_event_links(page)
        
        # Update index with new events
        for event_name, event_info, event_url in new_events:
            if event_url not in existing_events:
                existing_events[event_url] = {
                    'name': event_name,
                    'info': event_info,
                    'downloaded': False,
                    'has_location': False
                }
        
        # Save updated index
        save_to_index(existing_events)

        # Process events that need downloading
        for event_url, event_data in existing_events.items():
            if not event_data['downloaded'] or not event_data['has_location']:
                print(f"Processing {event_data['name']}")
                safe_name = sanitize_filename(event_data['name'])
                output_file = f"{OUTPUT_DIR}/{safe_name}.csv"
                
                try:
                    results, has_location = get_race_results(page, event_url)
                    
                    if has_location and results:
                        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                            writer = csv.writer(csvfile)
                            # Add event information as header rows
                            writer.writerow(["Event Name:", event_data['name']])
                            writer.writerow(["Event Information:", event_data['info']])
                            writer.writerow(["Event URL:", event_url])
                            writer.writerow([])  # Empty row for separation
                            writer.writerow(["Race Results:"])
                            for row in results:
                                writer.writerow(row)
                        
                        # Update index with success
                        existing_events[event_url]['downloaded'] = True
                        existing_events[event_url]['has_location'] = True
                        save_to_index(existing_events)
                    else:
                        print(f"Skipping {event_data['name']} - No location data available")
                        existing_events[event_url]['has_location'] = False
                        save_to_index(existing_events)
                    
                    time.sleep(1)  # polite delay
                except Exception as e:
                    print(f"Error with {event_url}: {e}")
                    # Don't update index on error, allowing for retry later

        browser.close()
