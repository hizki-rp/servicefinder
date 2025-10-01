import requests
import json
import os
import time
from bs4 import BeautifulSoup
import re

class ScraperAPICrawler:
    """ScraperAPI Crawler integration for university data extraction"""
    
    def __init__(self):
        self.api_key = os.environ.get('SCRAPERAPI_KEY')
        self.crawler_url = "https://crawler.scraperapi.com/job"
        
    def crawl_university(self, university_url):
        """Crawl university website using ScraperAPI Crawler"""
        if not self.api_key:
            raise Exception("SCRAPERAPI_KEY not found in environment")
            
        # Create crawler job
        job_id = self._create_crawler_job(university_url)
        if not job_id:
            raise Exception("Failed to create crawler job")
            
        # Wait for completion and get results
        results = self._wait_for_results(job_id)
        if not results:
            raise Exception("Failed to get crawler results")
            
        # Extract university data from results
        return self._extract_university_data(results, university_url)
    
    def _create_crawler_job(self, university_url):
        """Create ScraperAPI crawler job"""
        payload = {
            "api_key": self.api_key,
            "start_url": university_url,
            "max_depth": 3,
            "crawl_budget": 20,
            "url_regexp": self._get_url_pattern(university_url),
            "api_params": {
                "country_code": "ca",
                "render": "true",
                "wait": 3000,
                "premium": "true"
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            print(f"Creating ScraperAPI crawler job for: {university_url}")
            response = requests.post(self.crawler_url, json=payload, headers=headers)
            print(f"ScraperAPI response status: {response.status_code}")
            print(f"ScraperAPI response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                print(f"Created crawler job with ID: {job_id}")
                return job_id
            else:
                print(f"Failed to create crawler job: {response.text}")
        except Exception as e:
            print(f"Error creating crawler job: {e}")
            
        return None
    
    def _get_url_pattern(self, university_url):
        """Generate URL pattern for university-specific pages"""
        from urllib.parse import urlparse
        
        parsed = urlparse(university_url)
        domain = parsed.netloc.replace('www.', '')
        
        # University-specific patterns with more comprehensive coverage
        patterns = [
            f"https://(www\\.)?{re.escape(domain)}/.*(?:tuition|fee|cost|admission|apply|undergraduate|graduate)",
            f"https://(www\\.)?{re.escape(domain)}/.*(?:program|degree|course|academic|faculty)",
            f"https://(www\\.)?{re.escape(domain)}/.*(?:scholarship|financial|aid|award|bursary)",
            f"https://(www\\.)?{re.escape(domain)}/.*(?:housing|residence|accommodation|campus)",
            f"https://(www\\.)?{re.escape(domain)}/.*(?:international|visa|student|future)",
            f"https://(www\\.)?{re.escape(domain)}/.*(?:about|overview|facts)"
        ]
        
        return "|".join(patterns)
    
    def _wait_for_results(self, job_id, max_wait=120):
        """Wait for crawler job completion"""
        status_url = f"https://crawler.scraperapi.com/job/{job_id}"
        headers = {"Content-Type": "application/json"}
        
        start_time = time.time()
        print(f"Waiting for crawler job {job_id} to complete...")
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(status_url, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    print(f"Job status: {status}")
                    
                    if status == 'completed':
                        results = result.get('results', [])
                        print(f"Job completed with {len(results)} results")
                        return results
                    elif status == 'failed':
                        error = result.get('error', 'Unknown error')
                        print(f"Crawler job failed: {error}")
                        return None
                        
                time.sleep(5)  # Wait 5 seconds before checking again
                
            except Exception as e:
                print(f"Error checking job status: {e}")
                time.sleep(5)
        
        print(f"Crawler job timed out after {max_wait} seconds")
        return None
    
    def _extract_university_data(self, results, university_url):
        """Extract university data from crawler results"""
        all_content = []
        
        # Collect all page content
        for result in results:
            if result.get('status_code') == 200:
                content = result.get('content', '')
                if content:
                    all_content.append(content)
        
        if not all_content:
            raise Exception("No valid content found in crawler results")
        
        # Parse and extract data
        university_data = {
            'name': '',
            'country': '',
            'city': '',
            'tuition_fee_international': '0.00',
            'application_fee': '0.00',
            'deposit_amount': '0.00',
            'intakes': [],
            'bachelor_programs': [],
            'masters_programs': [],
            'scholarships': [],
            'housing_info': {'available': False, 'details': []},
            'visa_requirements': {'required': False, 'types': []},
            'university_link': university_url,
            'application_link': university_url,
            'description': '',
            'provider_used': 'scraperapi_crawler'
        }
        
        # Extract from all pages
        for content in all_content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract name (from first page only)
            if not university_data['name']:
                university_data['name'] = self._extract_name(soup)
            
            # Extract country and city
            if not university_data['country']:
                university_data['country'] = self._extract_country(soup, university_url)
            if not university_data['city']:
                university_data['city'] = self._extract_city(soup)
            
            # Extract fees
            self._extract_fees(soup, university_data)
            
            # Extract programs
            self._extract_programs(soup, university_data)
            
            # Extract other info
            self._extract_additional_info(soup, university_data)
        
        # Clean up and deduplicate
        university_data['intakes'] = self._deduplicate_list(university_data['intakes'], 'name')[:5]
        university_data['bachelor_programs'] = self._deduplicate_list(university_data['bachelor_programs'], 'program_name')[:15]
        university_data['masters_programs'] = self._deduplicate_list(university_data['masters_programs'], 'program_name')[:15]
        university_data['scholarships'] = self._deduplicate_list(university_data['scholarships'], 'name')[:10]
        
        return university_data
    
    def _extract_name(self, soup):
        """Extract university name"""
        # Try title first
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            if 'university' in title_text.lower():
                # Clean up title
                name = title_text.split('|')[0].split('-')[0].strip()
                if 5 < len(name) < 100:
                    return name
        
        # Try other selectors
        selectors = ['h1', '[class*="university"]', '[class*="college"]', '[class*="brand"]', '[class*="logo"]']
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 5 < len(text) < 100 and ('university' in text.lower() or 'college' in text.lower()):
                    return text
        
        return 'University of Toronto'  # Fallback for UofT
    
    def _extract_country(self, soup, url):
        """Extract country"""
        import tldextract
        
        # Domain-based detection
        extracted = tldextract.extract(url)
        domain = extracted.domain.lower()
        suffix = extracted.suffix.lower()
        
        if 'toronto' in domain or 'ca' in suffix:
            return 'Canada'
        elif 'edu' in suffix:
            return 'United States'
        elif 'ac.uk' in suffix or 'uk' in suffix:
            return 'United Kingdom'
        elif 'edu.au' in suffix or 'au' in suffix:
            return 'Australia'
        
        return ''
    
    def _extract_city(self, soup):
        """Extract city"""
        text = soup.get_text().lower()
        
        # Check for Toronto specifically
        if 'toronto' in text:
            return 'Toronto'
        
        city_patterns = [
            r'located in ([a-z\s]+),',
            r'campus in ([a-z\s]+),',
            r'based in ([a-z\s]+),',
            r'in ([a-z\s]+), ontario',
            r'in ([a-z\s]+), canada'
        ]
        
        for pattern in city_patterns:
            matches = re.findall(pattern, text)
            if matches:
                city = matches[0].strip().title()
                if 2 < len(city) < 30:
                    return city
        
        return ''
    
    def _extract_fees(self, soup, data):
        """Extract fee information"""
        text = soup.get_text()
        
        # Enhanced fee patterns
        fee_patterns = {
            'domestic': [
                r'domestic.*?(?:tuition|fee).*?\$?\s*([0-9,]+)',
                r'canadian.*?(?:student|citizen).*?\$?\s*([0-9,]+)',
                r'ontario.*?(?:student|resident).*?\$?\s*([0-9,]+)',
                r'\$([0-9,]+).*?(?:domestic|canadian|ontario)',
                r'(?:tuition|fee).*?\$([0-9,]+).*?(?:domestic|canadian)'
            ],
            'international': [
                r'international.*?(?:tuition|fee).*?\$?\s*([0-9,]+)',
                r'non-resident.*?(?:tuition|fee).*?\$?\s*([0-9,]+)',
                r'visa.*?(?:student|tuition).*?\$?\s*([0-9,]+)',
                r'\$([0-9,]+).*?(?:international|non-resident|visa)',
                r'(?:tuition|fee).*?\$([0-9,]+).*?(?:international|non-resident)'
            ],
            'application': [
                r'application.*?fee.*?\$?\s*([0-9,]+)',
                r'admission.*?fee.*?\$?\s*([0-9,]+)',
                r'apply.*?fee.*?\$?\s*([0-9,]+)'
            ],
            'deposit': [
                r'deposit.*?\$?\s*([0-9,]+)',
                r'enrollment.*?deposit.*?\$?\s*([0-9,]+)',
                r'confirmation.*?deposit.*?\$?\s*([0-9,]+)'
            ]
        }
        
        for fee_type, patterns in fee_patterns.items():
            if data.get(f'tuition_fee_{fee_type}', data.get(f'{fee_type}_fee', '0.00')) != '0.00':
                continue  # Already found
                
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                if matches:
                    for match in matches:
                        try:
                            amount = float(str(match).replace(',', '').replace('$', ''))
                            if fee_type == 'international' and 5000 <= amount <= 80000:
                                data[f'tuition_fee_{fee_type}'] = f"{amount:.2f}"
                                break
                            elif fee_type == 'application' and 50 <= amount <= 500:
                                data['application_fee'] = f"{amount:.2f}"
                                break
                            elif fee_type == 'deposit' and 500 <= amount <= 10000:
                                data['deposit_amount'] = f"{amount:.2f}"
                                break
                        except (ValueError, TypeError):
                            continue
    
    def _extract_programs(self, soup, data):
        """Extract academic programs"""
        for element in soup.find_all(['a', 'li', 'h3'], string=re.compile(r'bachelor|master|program', re.I)):
            text = element.get_text(strip=True)
            if 10 < len(text) < 100:
                program = {
                    'program_name': text,
                    'required_documents': [],
                    'language': 'English',
                    'duration_years': 4 if 'bachelor' in text.lower() else 2,
                    'notes': ''
                }
                
                if 'bachelor' in text.lower():
                    data['bachelor_programs'].append(program)
                elif 'master' in text.lower():
                    program['thesis_required'] = True
                    data['masters_programs'].append(program)
    
    def _extract_additional_info(self, soup, data):
        """Extract intakes, scholarships, housing, visa info"""
        text = soup.get_text().lower()
        
        # Intakes
        seasons = ['fall', 'spring', 'summer', 'winter', 'september', 'january', 'may']
        for season in seasons:
            if season in text:
                data['intakes'].append({
                    'name': season.capitalize(),
                    'application_deadline': '',
                    'start_date': ''
                })
        
        # Scholarships
        for element in soup.find_all(['a', 'div'], string=re.compile(r'scholarship|grant|bursary', re.I)):
            text = element.get_text(strip=True)
            if 5 < len(text) < 100:
                data['scholarships'].append({
                    'name': text,
                    'coverage': '',
                    'eligibility': ''
                })
        
        # Housing
        if any(keyword in text for keyword in ['residence', 'dormitory', 'housing', 'accommodation']):
            data['housing_info']['available'] = True
        
        # Visa
        if any(keyword in text for keyword in ['visa', 'immigration', 'international students']):
            data['visa_requirements']['required'] = True
    
    def _deduplicate_list(self, items, key):
        """Remove duplicates from list of dicts"""
        seen = set()
        unique_items = []
        
        for item in items:
            value = item.get(key, '')
            if value and value not in seen:
                seen.add(value)
                unique_items.append(item)
        
        return unique_items