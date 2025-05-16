import requests
import pandas as pd
import time
import csv
import os

# 1. Get list of events


def get_events(page=1):
    url = "https://rmsprodapi.nyrr.org/api/v2/events/search"
    payload = {
        "searchString": None,
        "distance": None,
        "year": None,
        "notOlderDays": None,
        "sortColumn": "StartDateTime",
        "sortDescending": 1,
        "pageIndex": page,
        "pageSize": 51
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["items"]


def get_total_events():
    url = "https://rmsprodapi.nyrr.org/api/v2/events/search"
    payload = {
        "searchString": None,
        "distance": None,
        "year": None,
        "notOlderDays": None,
        "sortColumn": "StartDateTime",
        "sortDescending": 1,
        "pageIndex": 1,
        "pageSize": 51
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["totalItems"]


def get_total_finishers(event_code, page=1, page_size=51):
    url = "https://rmsprodapi.nyrr.org/api/v2/runners/finishers-filter"
    payload = {
        "eventCode": event_code,
        "sortColumn": "overallTime",
        "sortDescending": False,
        "pageIndex": page,
        "pageSize": page_size
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["totalItems"]

# 2. Get finishers for an event code


def get_finishers(event_code, page=1, page_size=51):
    url = "https://rmsprodapi.nyrr.org/api/v2/runners/finishers-filter"
    payload = {
        "ageFrom" :  None,
        "ageGradedPerformanceFrom" :  None, 
        "ageGradedPerformanceTo" :  None,
        "ageGradedPlaceFrom" :  None,
        "ageGradedPlaceTo" :  None,
        "ageGradedTimeFrom" :  None,
        "ageGradedTimeTo" :  None,
        "ageTo" :  None,
        "city" :  None,
        "countryCode" :  None,
        "gender" :  None,
        "gunTimeFrom" :  None,
        "gunTimeTo" :  None,
        "handicap" :  None,
        "overallPlaceFrom" :  None,
        "overallPlaceTo" :  None,
        "overallTimeFrom" :  None,
        "overallTimeTo" :  None,
        "paceFrom" :  None,
        "paceTo" :  None,
        "searchString" :  None,
        "stateProvince" :  None,
        "teamCode" :  None,
        "teamName" :  None,
        "eventCode": event_code,
        "sortColumn": "overallTime",
        "sortDescending": False,
        "pageIndex": page,
        "pageSize": page_size
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def sanitize_filename(name):
    """Convert a string into a valid filename by replacing non-alphanumeric chars with underscores."""
    return ''.join(c if c.isalnum() else '_' for c in name).strip('_')

def save_event_results(event, results, output_dir="output"):
    """Save event information and results to a CSV file."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a sanitized filename from the event name
    safe_name = sanitize_filename(event.get('name', event['eventName']))
    output_file = os.path.join(output_dir, f"{safe_name}.csv")
    
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        
        # Write event information headers
        writer.writerow(["Event Name:", event.get('eventName', '')])
        writer.writerow(["Event Code:", event.get('eventCode', '')])
        writer.writerow(["Distance Name:", event.get('distanceName', '')])
        writer.writerow(["distanceUnitCode :", event.get('distanceUnitCode', '')])
        writer.writerow(["location :", event.get('venue', '')])
        writer.writerow(["startDateTime :", event.get('startDateTime', '')])
        writer.writerow(["Link:", f'https://results.nyrr.org/event/{event["eventCode"]}/finishers'])
        # writer.writerow(["virtualStartDate :", event.get('virtualStartDate', '')])
        # writer.writerow(["virtualEndDate :", event.get('virtualEndDate', '')])
        writer.writerow([])  # Empty row for separation
        
        if results:
            # Write results header
            writer.writerow(["Race Results:"])
            # Get headers from the first result
            headers = list(results[0].keys())
            writer.writerow(headers)
            
            # Write all results
            for result in results:
                writer.writerow([result.get(header, '') for header in headers])
        
        print(f"Saved results to {output_file}")

if __name__ == "__main__":
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all events
    totalEvents = get_total_events()
    print(f"Total events: {totalEvents}")
    allEvents = []
    
    for i in range(1, totalEvents//51 + 2):
        events = get_events(page=i)
        allEvents.extend(events)
    
    # Process each event
    for event in allEvents:
        try:
            print(f"Scraping {event['eventCode']} - {event.get('name', '')}")
            total_finishers = get_total_finishers(event["eventCode"])
            print(f"Total finishers: {total_finishers}")
            
            allResults = []
            for page in range(1, 11):
                try:
                    time.sleep(1)  # 1 second delay between requests
                    finishers = get_finishers(event["eventCode"], page=page, page_size=51)["items"]
                    allResults.extend(finishers)
                    print(f"Retrieved page {page} ({len(finishers)} results)")
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching page {page} for event {event['eventCode']}: {e}")
                    continue
            
            # Save event information and results
            save_event_results(event, allResults)
            
        except requests.exceptions.RequestException as e:
            print(f"Error processing event {event['eventCode']}: {e}")
            continue
