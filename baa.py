"""Web scraper for marathonguide.com to extract race results and event information."""
import csv
import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://results.baa.org/"


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
def scrape_marathon_results_before2018(page):
    results = []
    # Select all result rows (both active and inactive)
    row_selectors = "table.list-table tbody tr"
    row_elements = page.locator(row_selectors)
    count = row_elements.count()
    print(f"Found {count} rows")
    for i in range(count):
        row = row_elements.nth(i)
        cols = row.locator("td").all_inner_texts()
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
def scrape_results_header_before2018(page):
    # Select all result rows (both active and inactive)
    row_selectors = "table.list-table thead tr"
    row = page.locator(row_selectors)
    cols = row.locator("th").all_inner_texts()
    print(f'header:{cols}')
    return cols
def go_to_next_page(page, pageUrl):
    print('Checking for next page...')
    # Find the next page button
    next_button = page.locator('a.pages-nav-button', has_text=">")
    if next_button.is_visible():
        print(f"Navigating to next page...:{next_button}")
        href=next_button.get_attribute('href')
        url=pageUrl+href
        print(f"url: {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        return True
    return False


def scrape_event_links(page, year=2024,  group="runner", subgroup="R", gender="M", agegroup="%", results_page='25' ):

    try:
        # Increase timeout to 60 seconds and add error handling
        # page.goto(BASE_URL, timeout=60000)
        print(f'year: {year}')
        pageUrl=f"{BASE_URL}/{year}/"
        page.goto(pageUrl, timeout=40000)
        if(year>="2021"):
            page.select_option('select#default-lists-event_main_group', value=group)
            time.sleep(1)
            page.select_option('select#default-lists-event', value=subgroup)
            time.sleep(1)
            page.select_option('select#default-lists-sex', value=gender)
            time.sleep(1)
            # page.select_option('select#default-lists-age_class', value=agegroup)
            time.sleep(1)
            page.select_option('select#default-num_results', value=results_page)
            page.click('button#default-submit', timeout=30000)
            time.sleep(3)
        elif(year=="2020"):
            page.select_option('select#default-lists-event_main_group', value=group)
            time.sleep(1)
            page.select_option('select#default-lists-event', value=subgroup)
            page.fill('input#default-lists-sex', gender)
            # page.select_option('select#default-lists-age_class', value=agegroup)
            page.select_option('select#default-num_results', value=results_page)
            page.click('button#default-submit', timeout=30000)
            time.sleep(3)
        elif(year=="2019" or year =="2018"):
            page.select_option('select#default-lists-event', value=group)
            time.sleep(1)
            # page.select_option('select#default-lists-event', value=subgroup)
            page.select_option('select#default-lists-sex', value=gender)
            time.sleep(1)
            # page.select_option('select#default-lists-age_class', value=agegroup)
            time.sleep(1)
            page.select_option('select#default-num_results', value=results_page)
            time.sleep(1)
            page.click('button#default-submit', timeout=30000)
            time.sleep(3)
        elif(year == "2012" or year == "2013" or year == "2014"):
            page.select_option('select#lists-event', value=group)
            time.sleep(1)
            # page.select_option('select#default-lists-event', value=subgroup)
            page.select_option('select#lists-sex', value=gender)
            time.sleep(1)
            # page.select_option('select#lists-ageclass', value=agegroup)
            time.sleep(1)
            page.select_option('#form_lists_default select#num_results', value=results_page)
            time.sleep(1)
            page.click('#form_lists_default button#submit', timeout=30000)
            time.sleep(3)
        elif(year < "2018" and year != "2012"):
            page.select_option('select#fe-lists-event', value=group)
            time.sleep(1)
            # page.select_option('select#default-lists-event', value=subgroup)
            page.select_option('select#fe-lists-sex', value=gender)
            time.sleep(1)
            # page.select_option('select#fe-lists-ageclass', value=agegroup)
            time.sleep(1)
            page.select_option('select#fe-lists-num-results', value=results_page)
            time.sleep(1)
            page.click('input[value="show results"]', timeout=30000)
            time.sleep(3)

        allResults=[]
        if(year>="2018"):
            header= scrape_results_header(page)
            allResults.append(header)
            while True:
                results = scrape_marathon_results(page)
                if not results:
                    break
                allResults.extend(results)
                if not go_to_next_page(page, pageUrl):
                    break
        else:
            header = scrape_results_header_before2018(page)
            allResults.append(header)
            while True:
                results = scrape_marathon_results_before2018(page)
                if not results:
                    break
                allResults.extend(results)
                if not go_to_next_page(page, pageUrl):
                    break
        return allResults
    except Exception as e:
        print(f"Error accessing : {str(e)}")
        return []


if __name__ == "__main__":

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Set user agent
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })
        year='2025'
        # group="runner"
        # subgroup="R"
        # subgroup="PCT61"
        # subgroup="PCT62"
        # subgroup="PCT45"
        # subgroup="PCT35"
        # subgroup="PCT20"
        # subgroup="PCT13"
        # subgroup="PCT11"
        # group="wheelchair"
        # subgroup="P5"
        # subgroup="P6"
        # group="handcycle"
        # subgroup="H"
        group="duoteam"
        subgroup="DT"

        gender="W"
        agegroup="%"
        results_page='1000'
        
        # Get all events first
        allEvents = scrape_event_links(page, year, group, subgroup, gender, agegroup, results_page)
        print(f'allEvents: {allEvents}')
    
        try:
            safe_name = sanitize_filename(f"{group}_{subgroup}_{gender}")
            output_file = f"output/{year}_{safe_name}.csv"
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                # Add event information as header rows
                writer.writerow(["Event Information:"])
                writer.writerow(["Name: The Boston Marathon" ])
                writer.writerow(["Year:", year])
                writer.writerow(["Group:", group])
                writer.writerow(["Subgroup:", subgroup])
                writer.writerow(["Gender:", gender])
                writer.writerow(["Age Group:", agegroup])
                writer.writerow(["Link:", f'https://results.baa.org/{year}/?pid=list'])

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
            print(f"Error with {group}: {e}")
        browser.close()
