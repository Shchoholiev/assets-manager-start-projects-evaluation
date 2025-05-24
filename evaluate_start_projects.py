import csv
import requests
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# File paths
INPUT_CSV = "100_start_projects.csv"        # CSV with headers: ProjectDescription,AssetsUsed
OUTPUT_CSV = "100_start_projects_results_gpt-4.1-nano.csv"  # Output CSV that will be written row by row
API_URL = "https://host.docker.internal:7259/start-projects"

def compare_assets(expected_str, returned_assets):
    """
    Compare expected asset names (comma separated string) to the list of returned asset names.
    Returns (expected_list, returned_list, matched) where matched is True if the sets match.
    """
    expected_list = [asset.strip() for asset in expected_str.split(",") if asset.strip()]
    returned_list = [asset.get("name", "").strip() for asset in returned_assets]
    
    matched = set(expected_list) == set(returned_list)
    
    return expected_list, returned_list, matched

def process_projects():
    with open(f"output/{OUTPUT_CSV}", "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["ProjectDescription", "Expected Assets", "Returned Assets", "Matched"])
        outfile.flush()
        
        with open(f"input/{INPUT_CSV}", "r", newline="", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                project_description = row["ProjectDescription"]
                expected_assets_str = row["AssetsUsed"]
                
                payload = {"prompt": project_description}
                returned_assets = []
                try:
                    response = requests.post(API_URL, json=payload, verify=False)
                    response.raise_for_status()
                    
                    response_data = response.json()
                    returned_assets = response_data.get("codeAssets", [])
                except Exception as e:
                    print(f"Error processing project '{project_description}': {e}")
                
                expected_list, returned_list, matched = compare_assets(expected_assets_str, returned_assets)
                
                expected_str_clean = ",".join(expected_list)
                returned_str_clean = ",".join(returned_list)
                matched_str = "true" if matched else "false"
                
                writer.writerow([project_description, expected_str_clean, returned_str_clean, matched_str])
                outfile.flush()
                print(f"Processed project: {project_description}")
                
                time.sleep(0.2)

if __name__ == "__main__":
    process_projects()
