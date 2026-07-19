import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# =====================================================
# CONFIGURATION
# =====================================================
INPUT_EXCEL = "submissions.xlsx"
INPUT_SHEET = "Form Responses 1"     
OUTPUT_EXCEL = "Guided_Project_Evaluation_Final.xlsx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

MAX_WORKERS = 10     
REQUEST_TIMEOUT = 10

session = requests.Session()
session.headers.update(HEADERS)

# =====================================================
# COURSERA AGENT (FIXED DATE EXTRACTION)
# =====================================================
def coursera_agent(url):
    data = {
        "Coursera Valid": "No",
        "Coursera Name": None,
        "Completion Date": None
    }

    if not isinstance(url, str) or "coursera.org" not in str(url):
        return data

    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return data

        soup = BeautifulSoup(r.text, "html.parser")
        data["Coursera Valid"] = "Yes"

        # --- NAME EXTRACTION ---
        # Strategy: Look for strong/h1 tags common in certificates
        name_tag = soup.find("strong") or soup.find("h1") 
        if name_tag:
            raw_name = name_tag.get_text(strip=True)
            # Cleanup common phrases to leave just the name
            clean_name = raw_name.replace("Certificate", "").replace("for", "").strip()
            data["Coursera Name"] = clean_name

        # --- DATE EXTRACTION (FIXED) ---
        # Strategy: Find element containing "Completed on" directly
        date_element = soup.find(string=re.compile("Completed on"))
        
        if date_element:
            # If found text like "Completed on Jan 20, 2026", clean it
            date_text = date_element.replace("Completed on", "").strip()
            data["Completion Date"] = date_text
        else:
            # Fallback: Regex search on the whole text if specific element not found
            all_text = soup.get_text(" ", strip=True)
            match = re.search(r"Completed on\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", all_text, re.IGNORECASE)
            if match:
                data["Completion Date"] = match.group(1).strip()
            else:
                # Last resort: Look for just a date pattern (e.g. "Nov 12, 2024")
                match_alt = re.search(r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", all_text)
                if match_alt:
                    data["Completion Date"] = match_alt.group(1).strip()

    except Exception as e:
        print(f"Error Coursera: {e}")

    return data

# =====================================================
# LINKEDIN AGENT (CLEANER OUTPUT)
# =====================================================
def linkedin_agent(url):
    data = {
        "LinkedIn Valid": "No",
        "Post Date": None
    }

    if not isinstance(url, str) or "linkedin.com" not in str(url):
        return data

    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        
        if r.status_code == 200:
            data["LinkedIn Valid"] = "Yes"
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Extract date text
            post_date = None
            
            # Attempt 1: <time> tag
            time_tag = soup.find("time")
            if time_tag:
                post_date = time_tag.get_text(strip=True)
            else:
                # Attempt 2: Text search for relative times
                text = soup.get_text(" ", strip=True)
                match = re.search(r"(\d+[mo|w|d|h])", text) # Matches 1w, 2d, 5h
                if match:
                    post_date = match.group(1)

            # Cleanup: Remove "Edited" or extra junk
            if post_date:
                data["Post Date"] = post_date.replace("Edited", "").replace("•", "").strip()

    except Exception:
        pass

    return data

# =====================================================
# HELPERS
# =====================================================
def identity_agent(coursera_name):
    if coursera_name and len(coursera_name) > 2:
        return "Verified"
    return "Manual Check"

def marks_agent(coursera_valid, linkedin_valid, identity_status):
    if (coursera_valid == "Yes" and linkedin_valid == "Yes" and identity_status == "Verified"):
        return 2
    return 0

def process_row(row, coursera_col, linkedin_col, roll_col):
    c = coursera_agent(row[coursera_col])
    l = linkedin_agent(row[linkedin_col])
    
    identity = identity_agent(c["Coursera Name"])
    marks = marks_agent(c["Coursera Valid"], l["LinkedIn Valid"], identity)

    return {
        "Roll Number": row[roll_col],
        "Coursera Valid": c["Coursera Valid"],
        "Coursera Name": c["Coursera Name"], 
        "Completion Date": c["Completion Date"], # This should now be populated
        "LinkedIn Valid": l["LinkedIn Valid"],
        "Post Date": l["Post Date"],
        "Identity Status": identity,
        "Marks (Out of 2)": marks
    }

# =====================================================
# MAIN PIPELINE
# =====================================================
def run_pipeline():
    print("📥 Reading Excel...")
    try:
        df = pd.read_excel(INPUT_EXCEL, sheet_name=INPUT_SHEET)
    except Exception:
        print(f"⚠️ Could not find sheet '{INPUT_SHEET}'. Reading first sheet.")
        df = pd.read_excel(INPUT_EXCEL)

    # Clean headers
    df.columns = df.columns.str.strip()

    # Dynamic column finding
    try:
        coursera_col = [c for c in df.columns if "coursera" in c.lower()][0]
        linkedin_col = [c for c in df.columns if "linkedin" in c.lower()][0]
        roll_col = [c for c in df.columns if "roll" in c.lower()][0]
    except IndexError:
        print("❌ Error: Missing columns. Check headers.")
        return

    print(f"✅ Processing {len(df)} students...")
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_row, row, coursera_col, linkedin_col, roll_col) for _, row in df.iterrows()]
        
        for i, future in enumerate(as_completed(futures)):
            res = future.result()
            results.append(res)
            # Print live update every 5 rows
            if i % 5 == 0:
                print(f"   Row {i+1}: {res['Roll Number']} -> Date: {res['Completion Date']}")

    output_df = pd.DataFrame(results)
    if "Roll Number" in output_df.columns:
        output_df.sort_values("Roll Number", inplace=True)

    output_df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"\n✅ DONE! Saved to: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    run_pipeline()