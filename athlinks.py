"""Web scraper for marathonguide.com to extract race results and event information."""
import requests
import csv
import re
import time
import os
import json
import math
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.athlinks.com/"


def sanitize_filename(name):
    """Convert a string into a valid filename by replacing non-alphanumeric chars with underscores."""
    # Replace non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')

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
    results = response.json()
    return results
def scrape_event_info(event_id):
    url = f"https://alaska.athlinks.com/Events/Api/Merged/{event_id}"
    response = requests.get(url)
    response.raise_for_status()
    event_info = response.json()
    return event_info
def scrape_masterEvent_info(event_id):
    url = f"https://alaska.athlinks.com/MasterEvents/Api/{event_id}"
    response = requests.get(url)
    response.raise_for_status()
    event_info = response.json()
    return event_info
def get_total_results(event_id,event_course_id):
    url=f"https://results.athlinks.com/event/{event_id}?eventCourseId={event_course_id}&divisionId=&intervalId=&from=0&limit=50"
    response = requests.get(url)
    response.raise_for_status()
    totalResults = response.json()[0]["totalAthletes"]
    return totalResults
def calculate_pace(time_ms, distance_m, round_seconds=True):
    # Constants
    METERS_IN_MILE = 1609.344
    # Convert time to minutes
    time_minutes = time_ms / 1000 / 60
    # Convert distance to miles
    distance_miles = distance_m / METERS_IN_MILE
    # Calculate pace in minutes per mile
    pace_minutes = time_minutes / distance_miles
    # Split into minutes and seconds
    minutes = int(pace_minutes)
    seconds = pace_minutes - minutes
    if round_seconds:
        seconds = round(seconds * 60)
    else:
        seconds = int(seconds * 60)
    # Adjust for rounding overflow (e.g., 3:60 -> 4:00)
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02}"


def save_event_results(event, results, output_dir="output"):
     # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    safe_name = sanitize_filename(event.get('name', event['Name']))
    safe_time = sanitize_filename(results[0]["eventCourseName"])
    output_file = os.path.join(output_dir, f"{safe_name}_{safe_time}.csv")
    eventInfo = scrape_event_info(event["EventId"])
    location = eventInfo["result"]["location"]
    athlinksMasterId = eventInfo["result"]["athlinksMasterId"]
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        print(f'results:{results[0]}')
        writer.writerow(["Event Information:"])
        writer.writerow(["Event Course Name:", results[0]["eventCourseName"]])
        writer.writerow(["Location:", location["city"] + ", " + location["regionName"]+", " + location["country"]])
        writer.writerow(["page Link:", f'https://www.athlinks.com/event/{athlinksMasterId}/results/Event/{event["EventId"]}/Course/{event["EventCourseId"]}/Results'])
        for k, v in event.items():
            writer.writerow([k, v])
        writer.writerow([])  # Empty row for separation
        writer.writerow(["Race Results:"])

        headers = ["DisplayName","Overall", "Gender", "Division", "Pace", "Time"]
        writer.writerow(headers)
        for result in results[0]["interval"]["intervalResults"]:
            pace = result["pace"]
            distance = pace["distance"]["distanceInMeters"]
            milliseconds = pace["time"]["timeInMillis"]
            total_seconds = math.ceil(milliseconds / 1000)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            # Format as mm:ss
            formatted_pace = calculate_pace(milliseconds, distance, round_seconds=False)
            formatted_time = f"{minutes}:{seconds:02d}"
            writer.writerow([result["displayName"],
                            result["overallRank"],
                            result["genderRank"],
                            result["primaryBracketRank"],
                            formatted_pace,
                            formatted_time])                            
                            
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
        # print(f'allEvents:{allEvents}')
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
