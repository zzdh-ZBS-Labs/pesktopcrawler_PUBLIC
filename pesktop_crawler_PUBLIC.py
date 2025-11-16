import requests
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urljoin
import time
import random
from datetime import datetime
import os

# Realistic user agent to avoid detection
HEADERS = {
    'User-Agent': '<INSERTUSERAGENTHERE>',
    'Accept': '<INSERTYOURHEADERINFO>',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
}

BASE_URL = '<INSERTBASECRAWLURLHERE>'

def extract_ad_urls_from_plaintext(plaintext_source):
    """
    Extract <VARIABLESTORINGLINK> from plain text page source.
    Searches for patterns like: const <VARIABLESTORINGLINK> = "https://..."
    """
    ad_urls = {}
    
    # Debug: Show snippet to verify we have plain text
    snippet = plaintext_source[:500].replace('\n', ' ')
    print(f"    Source snippet: {snippet[:100]}...")
    
    # Simple regex patterns for plain text JavaScript variables
    # Looking for: const <VARIABLESTORINGLINK> = "URL" or const <VARIABLESTORINGLINK> = 'URL'
    patterns = {
        '<VARIABLESTORINGLINK>': r'const\s+<VARIABLESTORINGLINK>\s*=\s*["\']([^"\']+)["\']',
       }
    
    for var_name, pattern in patterns.items():
        match = re.search(pattern, plaintext_source, re.IGNORECASE)
        if match:
            url = match.group(1).strip()
            # Filter out empty or invalid URLs
            if url and url not in ['', '#', 'null', 'undefined', 'javascript:void(0)']:
                ad_urls[var_name] = url
                
                # Show the context where we found it
                match_pos = match.start()
                context_start = max(0, match_pos - 30)
                context_end = min(len(plaintext_source), match_pos + 100)
                context = plaintext_source[context_start:context_end]
                # Clean up whitespace for display
                context_clean = ' '.join(context.split())
                print(f"    ✓ Found {var_name}: ...{context_clean}...")
    
    return ad_urls

def get_software_title(plaintext_source):
    """Extract title from plain text HTML source"""
    # Try to find title in h1 tag
    h1_match = re.search(r'<h1[^>]*>(.+?)</h1>', plaintext_source, re.IGNORECASE | re.DOTALL)
    if h1_match:
        title = h1_match.group(1)
        # Remove HTML tags
        title = re.sub(r'<[^>]+>', '', title)
        # Clean up
        title = title.strip()
        title = re.sub(r'^Download\s+', '', title)
        title = re.sub(r'\s+for\s+(Windows|Mac|Android).*$', '', title)
        return title
    
    # Fallback to title tag
    title_match = re.search(r'<title>(.+?)</title>', plaintext_source, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'^Download\s+', '', title)
        return title
    
    return "Unknown"
    
def remove_duplicates(results):
    """
    Remove duplicate entries based on Download URL.
    Keeps the first occurrence of each unique download URL.
    """
    seen_urls = set()
    unique_results = []
    duplicates_removed = 0
    
    for entry in results:
        download_url = entry['Download URL']
        if download_url not in seen_urls:
            seen_urls.add(download_url)
            unique_results.append(entry)
        else:
            duplicates_removed += 1
    
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate download URLs")
    
    return unique_results
    
def create_output_folder():
    """
    Create a timestamped folder for output files.
    Format: YYYY-MM-DD_HHMMSS
    Returns the folder path.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder_name = f"pesktop_samples_{timestamp}"
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"✓ Created output folder: {folder_name}")
    
    return folder_name


def get_software_links_from_sections(base_url):
    """Get all software links from the main page"""
    software_urls = []
    
    print(f"Fetching main page: {base_url}")
    
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Get plain text source
        plaintext_source = response.text
        
        print(f"✓ Retrieved page ({len(plaintext_source)} bytes)")
        print("\nSearching for section_label_v2...")
        
        # Check if section_label_v2 exists
        if 'section_label_v2' in plaintext_source:
            print("✓ Found 'section_label_v2' in source!")
        else:
            print("✗ 'section_label_v2' not found, trying alternative approach...")
        
        # Parse to find links
        soup = BeautifulSoup(plaintext_source, 'html.parser')
        
        # Find divs with section_label_v2 class
        sections = soup.find_all('div', class_=lambda x: x and 'section_label_v2' in str(x))
        
        if sections:
            print(f"✓ Found {len(sections)} section_label_v2 divs")
            
            for idx, section in enumerate(sections, 1):
                # Get section name
                section_text = section.get_text(strip=True)[:50]
                print(f"\n  Section {idx}: {section_text}...")
                
                # Find all links in this section
                links = section.find_all('a', href=True)
                section_count = 0
                
                for link in links:
                    href = link.get('href')
                    # Match software detail page URLs
                    if href and re.match(r'/en/(windows|mac|systems|android)/[a-z0-9_-]+$', href):
                        full_url = urljoin(base_url, href)
                        if full_url not in software_urls and '/tag/' not in href:
                            software_urls.append(full_url)
                            section_count += 1
                
                print(f"    Found {section_count} software links")
        else:
            print("✗ No section_label_v2 divs found")
            print("  Falling back to finding all software links...")
            
            # Fallback: Get all software links
            links = soup.find_all('a', href=re.compile(r'/en/(windows|mac|systems|android)/[a-z0-9_-]+$'))
            for link in links:
                href = link.get('href')
                if href and '/tag/' not in href:
                    full_url = urljoin(base_url, href)
                    if full_url not in software_urls:
                        software_urls.append(full_url)
        
    except Exception as e:
        print(f"✗ Error fetching main page: {e}")
        import traceback
        traceback.print_exc()
    
    return software_urls

def crawl_pesktop(max_samples=None):
    """
    Main crawler function
    max_samples: Limit number of pages to crawl (None = all)
    """
    output_folder = create_output_folder()
    output_file = os.path.join(output_folder, 'pesktop_malware_samples.csv')
    
    print("="*70)
    print("PeskTop Malware Sample Crawler - ZBS Labs LLC")
    print("Plain Text Source Analysis")
    print("="*70)
    print(f"Output folder: {output_folder}")
    print(f"User Agent: {HEADERS['User-Agent'][:50]}...")
    print(f"Base URL: {BASE_URL}")
    if max_samples:
        print(f"Max samples: {max_samples}")
    print()
    
    # Step 1: Get software URLs
    print("="*70)
    print("STEP 1: Collecting software page URLs")
    print("="*70)
    software_urls = get_software_links_from_sections(BASE_URL)
    
    if max_samples and len(software_urls) > max_samples:
        print(f"\nLimiting to first {max_samples} URLs for testing...")
        software_urls = software_urls[:max_samples]
    
    print(f"\nTotal URLs to process: {len(software_urls)}")
    
    if len(software_urls) == 0:
        print("\n✗ No software links found. Exiting.")
        return []
    
    # Show sample URLs
    print("\nSample URLs:")
    for url in software_urls[:5]:
        print(f"  {url}")
    if len(software_urls) > 5:
        print(f"  ... and {len(software_urls) - 5} more")
    
    # Step 2: Extract <VARIABLESTORINGLINK> from each page
    results = []
    
    print("\n" + "="*70)
    print("STEP 2: Extracting <VARIABLESTORINGLINK> from plain text source")
    print("="*70)
    
    for idx, url in enumerate(software_urls, 1):
        print(f"\n[{idx}/{len(software_urls)}] {url}")
        
        try:
            # Get the page
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            # Get PLAIN TEXT source - this is key!
            plaintext_source = response.text
            
            print(f"  Source size: {len(plaintext_source)} bytes (plain text)")
            
            # Extract title from plain text
            title = get_software_title(plaintext_source)
            print(f"  Title: {title}")
            
            # Search plain text for <VARIABLESTORINGLINK> variables
            ad_urls = extract_ad_urls_from_plaintext(plaintext_source)
            
            if ad_urls:
                print(f"  ✓✓✓ FOUND {len(ad_urls)} MALWARE LINK(S)! ✓✓✓")
                for var_name, url_value in ad_urls.items():
                    print(f"      {var_name} = {url_value}")
                    results.append({
                        'Title': title,
                        'Page URL': url,
                        'Variable': var_name,
                        'Download URL': url_value
                    })
            else:
                print(f"  ✗ No <VARIABLESTORINGLINK> variables (no malware link)")
            
            # Be polite - delay between requests
            time.sleep(random.uniform(1.5, 3.0))
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
        # Step 3: Save results
    print("\n" + "="*70)
    print("STEP 3: Saving results")
    print("="*70)
    
    if results:
        # Remove duplicates BEFORE saving
        print(f"Total entries before deduplication: {len(results)}")
        results = remove_duplicates(results)
        print(f"Total unique entries after deduplication: {len(results)}")
        
        # Save CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Title', 'Page URL', 'Variable', 'Download URL'])
            writer.writeheader()
            writer.writerows(results)
        print(f"✓ Saved {len(results)} unique entries to {output_file}")
        for var_type in ['<VARIABLESTORINGLINK>']:
            filtered = [r for r in results if r['Variable'] == var_type]
            if filtered:
                filename = os.path.join(output_folder, f'malware_{var_type.lower()}_only.txt')
                with open(filename, 'w', encoding='utf-8') as f:
                    for entry in filtered:
                        f.write(f"{entry['Download URL']}\n")
                print(f"✓ Saved {len(filtered)} unique {var_type} URLs to {filename}")
        
    else:
        print("✗ No malware URLs found")
    
    return results, output_folder

if __name__ == "__main__":
    # For testing, limit to first 20 pages
    # Remove max_samples parameter to crawl all pages
    results, output_folder = crawl_pesktop(
        max_samples=20  # Remove this line or set to None for full crawl
    )
    
    print("\n" + "="*70)
    print("FINAL SUMMARY - ZBS Labs Malware Collection")
    print("="*70)
    print(f"Total malware samples found: {len(results)}")
    
    if results:
        print("\n" + "="*70)
        print("MALWARE SAMPLES READY FOR ANALYSIS:")
        print("="*70)
        
        for i, entry in enumerate(results, 1):
            print(f"\n{i}. {entry['Title']}")
            print(f"   Page: {entry['Page URL']}")
            print(f"   Variable: {entry['Variable']}")
            print(f"   Download: {entry['Download URL']}")
            print("\n" + "="*70)
            print("FINAL SUMMARY - ZBS Labs Malware Collection")
            print("="*70)
            print(f"Output folder: {output_folder}")
            print(f"Total malware samples found: {len(results)}")
            print("="*70)
            print("\nReady for analysis in your secured environments:")
            print("  - Bare-metal workstation")
            print("  - Multi-VM host")
            print("  - FlareVM setup")
    else:
        print("\nNo active malware slots found at this time.")
    
    print("\n" + "="*70)
    print("Crawl complete!")
    print("="*70)
