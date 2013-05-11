import time
import json
from functools import partial
from selenium.webdriver import Firefox

def scrape_candidate(browser, i):
    row = browser.find_element_by_css_selector("div.payment_pgdtls_inner table table tr:nth-child({0})".format(i))
    print "candidate {0} find all cells...".format((i - 1) / 2)
    cells = row.find_elements_by_css_selector("td")
    data = map(lambda c: c.text, cells)
    return dict(zip(("name", "party", "votes", "status"), data))

def scrape_candidates(browser):
    print "find all candidates..."
    rows = browser.find_elements_by_css_selector("div.payment_pgdtls_inner table table tr")
    return map(partial(scrape_candidate, browser), range(3, len(rows) + 1, 2))

def scrape_lightbox(browser):
    print "find table..."
    table = browser.find_element_by_css_selector("div.payment_pgdtls_inner")
    print "extract data..."
    data = map(lambda c: c.text, map(table.find_element_by_css_selector, (
        "tr:nth-child(1) > td:nth-child(2)", 
        "tr:nth-child(1) > td:nth-child(4)", 
        "tr:nth-child(2) > td:nth-child(2)",
        "tr:nth-child(2) > td:nth-child(4)",
        "tr:nth-child(3) > td:nth-child(2)",
    )))
    record = dict(zip((
        "total_registered_voters",
        "ballot_sheets_issued",
        "spoilt_votes",
        "unreturned_ballot_sheets",
        "voters_turnout",
    ), data))
    record["candidates"] = scrape_candidates(browser)
    return record

def scrape_row(browser, table_id, i):
    for attempt in range(10):
        try:
            row = browser.find_element_by_css_selector("#{0} tr:nth-child({1})".format(table_id, i))
            print "row {0} find all cells...".format(i - 1)
            cells = row.find_elements_by_css_selector("td")
            data = map(lambda c: c.text, cells)
        except:
            print "error occurred!!! retrying..."
        else:
            break
    else:
        data = ['' for i in range(6)]

    record = dict(zip(("constituency_code", "constituency_name", "state", "winner_name", "winner_party", "majority"), data))
    print "click row..."
    row = browser.find_element_by_css_selector("#{0} tr:nth-child({1})".format(table_id, i))
    row.click()
    record.update(scrape_lightbox(browser))
    print "close lightbox..."
    browser.find_element_by_id("cpaymnetcls").click()
    return record

def scrape_table(browser, table_id):
    print "find all rows..."
    rows = browser.find_elements_by_css_selector("#{0} tr".format(table_id))
    return map(partial(scrape_row, browser, table_id), range(2, len(rows) + 1))

def scrape_section(browser, section_name, total_page, page_link_id_prefix, table_id):
    print "scrape {0} section...".format(section_name)
    records = []
    for i in range(1, total_page + 1):
        print "click page " + str(i) + "..."
        link = browser.find_element_by_id(page_link_id_prefix + str(i))
        link.click()
        time.sleep(5)
        table = scrape_table(browser, table_id)
        for row in table:
            print row
            records.append(row)
    return records

def scrape_pru(browser, num, parliament_total_page, state_total_page):
    # records = scrape_section(browser, "parliament", parliament_total_page, "ContentPlaceHolder1_PlnkPage", "ContentPlaceHolder1_gridParliamentResul")
    # with open("pru{0}_parliament.json".format(num), 'w') as f:
    #     json.dump(records, f)
    records = scrape_section(browser, "state", state_total_page, "ContentPlaceHolder1_NlnkPage", "ContentPlaceHolder1_grdAssemblyResult")
    with open("pru{0}_state.json".format(num), 'w') as f:
        json.dump(records, f)

browser = Firefox()
print "open website..."
browser.get("http://www.pru13.com")
browser.implicitly_wait(30)
scrape_pru(browser, 13, 12, 33)
browser.find_element_by_id("tab_menu2").click()
scrape_pru(browser, 12, 23, 51)
