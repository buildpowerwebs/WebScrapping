"""Web scraper for marathonguide.com to extract race results and event information."""
import csv
import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.chicagomarathon.com/runners/race-results/"


def sanitize_filename(name):
    """Convert a string into a valid filename by replacing non-alphanumeric chars with underscores."""
    # Replace non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')

def scrape_marathon_results(page):
    results = []
    # Select all result rows (both active and inactive)
    row_selectors = "li.list-group-item.row:not(.list-group-header)"
    row_elements = page.locator(row_selectors)
    count = row_elements.count()
    print(f"Found {count} rows")
    for i in range(count):
        row = row_elements.nth(i)
        cols = row.locator('.list-field').all_inner_texts()
        print(f'cols:{cols}')
        results.append(cols)
    return results

def scrape_results_header(page):
    # Select all result rows (both active and inactive)
    row_selectors = "li.list-group-item.row.list-group-header"
    row = page.locator(row_selectors)
    cols = row.locator('.list-field').all_inner_texts()
    print(f'header:{cols}')
    return cols
def go_to_next_page(page, pageUrl):
    print('Checking for next page...')
    # Find the next page button
    next_button = page.locator('ul.pagination li.pages-nav-button a', has_text=">")
    if next_button.is_visible():
        print(f"Navigating to next page...:{next_button}")
        href=next_button.get_attribute('href')
        url=pageUrl+href
        print(f"url: {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        return True
    return False


def scrape_event_links(page, year=2024, event='marathon', group="runner", subgroup="MAR", gender="M", agegroup="-19", results_page='25' ):

    try:
        # Increase timeout to 60 seconds and add error handling
        # page.goto(BASE_URL, timeout=60000)
        print(f'year: {year}')
        if(year==2024):
            pageUrl="https://results.chicagomarathon.com/2024/"
            page.goto(pageUrl, timeout=30000)
            page.select_option('select[name="event_main_group"]', value=group)
            page.select_option('select[name="event"]', value=subgroup)
            page.select_option('select#default-lists-sex', value=gender)
            page.select_option('select#default-lists-age_class', value=agegroup)
            page.select_option('select#default-num_results', value=results_page)
            page.click('button#default-submit', timeout=30000)
            time.sleep(3)
            allResults=[]
            header= scrape_results_header(page)
            allResults.append(header)
            while True:
                results = scrape_marathon_results(page)
                if not results:
                    break
                allResults.extend(results)
                if not go_to_next_page(page, pageUrl):
                    break
            return allResults
        # else:
            # page.goto(BASE_URL, timeout=60000)
            # page.select_option('select[name="Year"]', value=str(year))
            # page.select_option('select[name="Event"]', value=event)
            # # Wait for the page to load after selecting options
            # page.wait_for_load_state('networkidle')
            # # Extract event links
            # event_links = page.locator('table.results-table a')
            # events = []
            # for i in range(event_links.count()):
            #     link = event_links.nth(i)
            #     event_name = link.inner_text().strip()
            #     event_url = link.get_attribute('href')
            #     event_info = f"{year} {event}" 
    except Exception as e:
        print(f"Error accessing {BASE_URL}: {str(e)}")
        return []


if __name__ == "__main__":

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Set user agent
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })
        year=2024
        event='marathon'
        group="wheelchair"
        subgroup="MAR"
        gender="M"
        agegroup="20"
        results_page='25'
        
        # Get all events first
        allEvents = scrape_event_links(page,  year, event, group, subgroup, gender, agegroup, results_page)
        print(f'allEvents: {allEvents}')
    
        try:
            safe_name = sanitize_filename(event)
            output_file = f"output/{year}{safe_name}.csv"
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                # Add event information as header rows
                writer.writerow(["Event Information:"])
                writer.writerow(["Year:", year])
                if not year==2024:
                    writer.writerow(["Event Name:", event])
                writer.writerow(["Group:", group])
                writer.writerow(["Subgroup:", subgroup])
                writer.writerow(["Gender:", gender])
                writer.writerow(["Age Group:", agegroup])
                writer.writerow([])  # Empty row for separation
                writer.writerow(["Race Results:"])
                try:
                    # results = scrape_event_links(page,  year, event, group, subgroup, gender, agegroup, results_page)
                    for row in allEvents:
                        writer.writerow(row)
                    time.sleep(1)  # polite delay
                except Exception as e:
                    print(f"Error with : {e}")
        except Exception as e:
            print(f"Error with {event}: {e}")
        #  for event_name, event_info, event_url in events:
        #     print(f"Scraping {event_name}")
        #     safe_name = sanitize_filename(event_name)
        #     output_file = f"output/{safe_name}.csv"
        #     with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        #         writer = csv.writer(csvfile)
        #         # Add event information as header rows
        #         writer.writerow(["Event Name:", event_name])
        #         writer.writerow(["Event Information:", event_info])
        #         writer.writerow([])  # Empty row for separation
        #         writer.writerow(["Race Results:"])
        #         try:
        #             results = get_race_results(page, event_url)
        #             for row in results:
        #                 writer.writerow(row)
        #             time.sleep(1)  # polite delay
        #         except Exception as e:
        #             print(f"Error with {event_url}: {e}")
        browser.close()
