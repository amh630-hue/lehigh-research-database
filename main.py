import requests
import pandas as pd
from datetime import datetime
import time

def fetch_nsf_data():
    print("Fetching NSF data...")
    url = "https://api.nsf.gov/services/v1/awards.json"
    awards_list = []
    offset = 1
    
    while True:
        params = {
            "awardeeName": '"Lehigh University"',
            "dateStart": "01/01/2010",
            "dateEnd": datetime.now().strftime("%m/%d/%Y"),
            "printFields": "id,title,abstractText,startDate,expDate,piFirstName,piLastName,piEmail,fundsObligatedAmt",
            "offset": offset,
            "rpp": 50
        }
        response = requests.get(url, params=params)
        if response.status_code != 200 or 'response' not in response.json():
            break
            
        awards = response.json()['response'].get('award', [])
        if not awards:
            break
            
        for award in awards:
            faculty_name = f"{award.get('piFirstName', '')} {award.get('piLastName', '')}".strip()
            award_id = award.get('id', '')
            awards_list.append({
                "Title": award.get('title', 'N/A'),
                "Abstract": award.get('abstractText', 'N/A'),
                "Start Date": award.get('startDate', 'N/A'),
                "End Date": award.get('expDate', 'N/A'),
                "Department at Lehigh": "Check Manually", 
                "Faculty Name": faculty_name if faculty_name else 'N/A',
                "Faculty Email": award.get('piEmail', 'N/A'),
                "Funding Agency": "National Science Foundation (NSF)",
                "Funding Amount": f"${award.get('fundsObligatedAmt', '0')}",
                "Link to Website": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={award_id}" if award_id else 'N/A',
                "Award Number": award_id,
                "Faculty Website": "N/A"
            })
        offset += 50
    return awards_list

def fetch_nih_data():
    print("Fetching NIH data...")
    url = "https://api.reporter.nih.gov/v2/projects/search"
    awards_list = []
    offset = 0
    
    while True:
        payload = {
            "criteria": {"org_names": ["LEHIGH UNIVERSITY"], "project_start_date": {"from_date": "2010-01-01"}},
            "include_fields": ["project_title", "abstract_text", "project_start_date", "project_end_date", "contact_pi_name", "award_amount", "project_num", "agency_ic_fundings"],
            "offset": offset,
            "limit": 500
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            break
            
        results = response.json().get('results', [])
        if not results:
            break
            
        for award in results:
            award_id = award.get('project_num', 'N/A')
            awards_list.append({
                "Title": award.get('project_title', 'N/A'),
                "Abstract": "Available in RePORTER",
                "Start Date": award.get('project_start_date', 'N/A')[:10] if award.get('project_start_date') else 'N/A',
                "End Date": award.get('project_end_date', 'N/A')[:10] if award.get('project_end_date') else 'N/A',
                "Department at Lehigh": "Check Manually",
                "Faculty Name": award.get('contact_pi_name', 'N/A'),
                "Faculty Email": "N/A",
                "Funding Agency": "National Institutes of Health (NIH)",
                "Funding Amount": f"${award.get('award_amount', '0')}",
                "Link to Website": f"https://reporter.nih.gov/project-details/{award_id}",
                "Award Number": award_id,
                "Faculty Website": "N/A"
            })
        offset += 500
    return awards_list

def fetch_usaspending_data():
    print("Fetching DOD, DOE, EPA, and other federal data from USAspending...")
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    awards_list = []
    page = 1
    
    while True:
        payload = {
            "filters": {
                "recipient_search_text": ["Lehigh University"],
                "award_type_codes": ["06", "07", "08", "09", "10", "11"] # Grant codes
            },
            "fields": ["Award ID", "Start Date", "End Date", "Award Amount", "Description", "Funding Agency", "Funding Sub Agency"],
            "page": page,
            "limit": 100
        }
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            break
            
        results = response.json().get('results', [])
        if not results:
            break
            
        for award in results:
            agency = award.get('Funding Agency', 'Unknown Federal Agency')
            sub_agency = award.get('Funding Sub Agency', '')
            full_agency = f"{agency} - {sub_agency}" if sub_agency else agency
            
            # Skip NSF and NIH to avoid duplicates since we already pulled them with better details above
            if "National Science Foundation" in full_agency or "National Institutes of Health" in full_agency:
                continue
                
            award_id = award.get('Award ID', 'N/A')
            awards_list.append({
                "Title": award.get('Description', 'N/A').title(),
                "Abstract": "See USAspending/Agency database for abstract.",
                "Start Date": award.get('Start Date', 'N/A'),
                "End Date": award.get('End Date', 'N/A'),
                "Department at Lehigh": "Check Manually",
                "Faculty Name": "Check USAspending/PAMS", # API doesn't return PI name
                "Faculty Email": "N/A",
                "Funding Agency": full_agency,
                "Funding Amount": f"${award.get('Award Amount', '0')}",
                "Link to Website": f"https://www.usaspending.gov/award/{award.get('generated_internal_id', '')}",
                "Award Number": award_id,
                "Faculty Website": "N/A"
            })
        page += 1
        time.sleep(1) # Prevent overloading the API
        
    return awards_list

def main():
    print("Starting data collection...")
    all_data = fetch_nsf_data() + fetch_nih_data() + fetch_usaspending_data()
    
    df = pd.DataFrame(all_data)
    
    # Drop exact duplicates if any exist
    df = df.drop_duplicates(subset=['Award Number'])
    
    filename = f"Lehigh_Research_Master_{datetime.now().strftime('%Y_%m_%d')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"\nSuccess! Saved {len(df)} research projects to {filename}")

if __name__ == "__main__":
    main()
