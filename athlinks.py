"""Web scraper for marathonguide.com to extract race results and event information."""
import requests
import csv
import re
import time
import os
import json
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.athlinks.com/"


def sanitize_filename(name):
    """Convert a string into a valid filename by replacing non-alphanumeric chars with underscores."""
    # Replace non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')

def save_events_to_csv(events, filename="marathon_events.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Event Name", "Information", "URL"])
        writer.writerows(events)


def signin(page, username, password):
    # 1. Go to Athlinks homepage
    page.goto("https://www.athlinks.com/", timeout=200000)
    # page.wait_for_load_state("networkidle")
    # time.sleep(2)
    print(f'signin')
    # 2. Click the "Sign In" button (by text or selector)
    href = page.get_attribute('a#sign-in', 'href')
    if href:
        page.goto(href)
    # Wait for the sign-in options to appear
    time.sleep(2)
    # 3. Click the "Email" button
    page.click('a#join-with-email', timeout=10000)
      # Wait for the form to appear
    time.sleep(1)

    # 4. Fill in the email and password fields
    page.fill('input#username', username)
    page.fill('input#password', password)

    # 5. Click the "Sign In" button to submit
    page.click('button#continue-button')
    # page.wait_for_load_state("networkidle")
    print("Signed in successfully.")


def get_events(keyword):
    url = f"https://alaska.athlinks.com/Result/api/Search?searchTerm={keyword}"
    response = requests.get(url)
    response.raise_for_status()
    events = response.json()["Result"]["RaceList"]
    # Suppose 'events' is your original list of lists
    flat_events = [item for sublist in events for item in sublist]
    return flat_events
def get_total_events(keyword):
    url = f"https://alaska.athlinks.com/Result/api/Search?searchTerm={keyword}"
    response = requests.get(url)
    response.raise_for_status()
    totalEvents = response.json()["Result"]["TotalCount"]
    return totalEvents

def scrape_race_results(event_id,event_course_id, fr=0):
    url=f"https://results.athlinks.com/event/{event_id}?eventCourseId={event_course_id}&divisionId=&intervalId=&from={fr}&limit=50"
    response = requests.get(url)
    response.raise_for_status()
    results = response.json()[0]["interval"]["intervalResults"]
    return results
def get_total_results(event_id,event_course_id):
    url=f"https://results.athlinks.com/event/{event_id}?eventCourseId={event_course_id}&divisionId=&intervalId=&from=0&limit=50"
    response = requests.get(url)
    response.raise_for_status()
    totalResults = response.json()[0]["totalAthletes"]
    return totalResults
def save_event_results(event, results, output_dir="output"):
     # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    safe_name = sanitize_filename(event.get('name', event['Name']))
    safe_time = sanitize_filename(event.get('time', event['Time']))
    output_file = os.path.join(output_dir, f"{safe_name}{safe_time}.csv")
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Event Information:"])
        for k, v in event.items():
            writer.writerow([k, v])
        writer.writerow([])  # Empty row for separation
        writer.writerow(["Race Results:"])

        headers = list(results[0].keys())
        writer.writerow(headers)
        for result in results:
            writer.writerow(result.values())
    print(f"Saved results to {output_file}")
if __name__ == "__main__":
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Set user agent
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })
        signin(page, 'buildpowerwebs01@gmail.com', 'kikkkikiilRgg9938!')

        totalEvents = get_total_events('marathon')
        allEvents= get_events('marathon')
        print(f'allEvents:{allEvents}')
        for event in allEvents:
            try:
                time.sleep(1)
                eventId=event["EventId"]
                eventCourseId=event["EventCourseId"]
                totalResults=get_total_results(eventId,eventCourseId)
                allResults=[]
                for i in range(0, totalResults//50+1):
                    results=scrape_race_results(eventId,eventCourseId,fr=i*50)
                    allResults.extend(results)
                time.sleep(1)
                save_event_results(event, allResults)
            except requests.exceptions.RequestException as e:
                print(f"Error processing event {event['eventCode']}: {e}")
                continue
     
        browser.close()
