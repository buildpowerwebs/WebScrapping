from playwright.sync_api import sync_playwright
import csv
import time

BASE_URL = "https://www.marathonguide.com/results/search.cfm"

def scrape_event_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Set a user agent
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })
        
        try:
            # Increase timeout to 60 seconds and add error handling
            page.goto(BASE_URL, timeout=60000)
        except Exception as e:
            print(f"Error accessing {BASE_URL}: {str(e)}")
            browser.close()
            return []
            
        # Keep clicking "Load More" until it's gone
        while True:
            try:
                load_more = page.locator("text=LOAD MORE")
                cnt=0
                if load_more.is_visible() and cnt<10:
                    load_more.click()
                    cnt=cnt+1
                    time.sleep(3)  # wait for content to load
                else:
                    break
            except:
                break

        # Extract event links
        event_elements = page.locator(".MuiBox-root .css-11pbu0q a")
        event_count = event_elements.count()
        print(f"Found {event_count} events")

        events = []
        for i in range(event_count):
            el = event_elements.nth(i)
            href = el.get_attribute("href")
            text = el.inner_text()
            if href and "browse.cfm?MIDD=" in href:
                events.append((text.strip(), f"https://www.marathonguide.com{href}"))

        browser.close()
        return events

def save_events_to_csv(events, filename="marathon_events.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Event Name", "URL"])
        writer.writerows(events)

if __name__ == "__main__":
    events = scrape_event_links()
    save_events_to_csv(events)
    print(f"Saved {len(events)} events to marathon_events.csv")
