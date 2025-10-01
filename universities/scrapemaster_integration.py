import requests
import json
import os
import re
from urllib.parse import urljoin

class ScrapeMasterIntegration:
    """Integration with ScrapeMaster using free resources"""
    
    def __init__(self):
        # Free ScrapingBee API (1000 requests/month free)
        self.scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
        
        # Free ScraperAPI (1000 requests/month free) 
        self.scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '')
        
        # Free Zenrows (1000 requests/month free)
        self.zenrows_key = os.environ.get('ZENROWS_API_KEY', '')
        
        # Backup: requests with headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape_with_scrapingbee(self, url):
        """Use ScrapingBee free tier"""
        if not self.scrapingbee_key:
            return None
            
        api_url = 'https://app.scrapingbee.com/api/v1/'
        params = {
            'api_key': self.scrapingbee_key,
            'url': url,
            'render_js': 'false',
            'premium_proxy': 'false'
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"ScrapingBee failed: {e}")
        return None

    def scrape_with_scraperapi(self, url):
        """Use ScraperAPI free tier"""
        if not self.scraperapi_key:
            return None
            
        api_url = 'http://api.scraperapi.com'
        params = {
            'api_key': self.scraperapi_key,
            'url': url,
            'render': 'false'
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"ScraperAPI failed: {e}")
        return None

    def scrape_with_zenrows(self, url):
        """Use Zenrows free tier"""
        if not self.zenrows_key:
            return None
            
        api_url = 'https://api.zenrows.com/v1/'
        params = {
            'apikey': self.zenrows_key,
            'url': url,
            'js_render': 'false',
            'premium_proxy': 'false'
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Zenrows failed: {e}")
        return None

    def scrape_with_requests(self, url):
        """Fallback using requests"""
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Requests failed: {e}")
        return None

    def get_page_content(self, url):
        """Try multiple free services in order"""
        
        # Try ScraperAPI first (you have this key)
        content = self.scrape_with_scraperapi(url)
        if content:
            return content, 'scraperapi'
            
        # Try Zenrows
        content = self.scrape_with_zenrows(url)
        if content:
            return content, 'zenrows'
            
        # Try ScrapingBee
        content = self.scrape_with_scrapingbee(url)
        if content:
            return content, 'scrapingbee'
            
        # Fallback to requests
        content = self.scrape_with_requests(url)
        if content:
            return content, 'requests'
            
        return None, None

    def extract_university_data(self, url):
        """Extract university data using ScrapeMaster approach"""
        content, provider = self.get_page_content(url)
        if not content:
            raise Exception("Failed to fetch page content")
            
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find and crawl relevant pages for better data
        fee_links = self._find_fee_pages(soup, url)
        admission_links = self._find_admission_pages(soup, url)
        
        # Crawl additional pages for detailed info
        all_soups = [soup]
        for link in (fee_links + admission_links)[:3]:
            try:
                page_content, _ = self.get_page_content(link)
                if page_content:
                    page_soup = BeautifulSoup(page_content, 'html.parser')
                    all_soups.append(page_soup)
            except:
                continue
        
        # Extract from all pages
        data = {
            'name': self._extract_name(soup),
            'country': self._extract_country(soup, url),
            'city': self._extract_city(soup),
            'tuition_fee_domestic': self._extract_fees_from_pages(all_soups, 'domestic'),
            'tuition_fee_international': self._extract_fees_from_pages(all_soups, 'international'),
            'application_fee': self._extract_fees_from_pages(all_soups, 'application'),
            'deposit_amount': self._extract_fees_from_pages(all_soups, 'deposit'),
            'intakes': self._extract_intakes_from_pages(all_soups),
            'programs': self._extract_programs_from_pages(all_soups),
            'scholarships': self._extract_scholarships_from_pages(all_soups),
            'housing_available': self._extract_housing_from_pages(all_soups),
            'visa_required': self._extract_visa_from_pages(all_soups),
            'provider_used': provider
        }
        
        return data

    def _extract_name(self, soup):
        """Extract university name"""
        selectors = [
            'h1',
            '[class*="university"]',
            '[class*="college"]',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 5 and len(text) < 100:
                    return text
        return ''

    def _extract_country(self, soup, url):
        """Extract country from URL or content"""
        import tldextract
        
        # Domain-based detection
        domain_countries = {
            'ca': 'Canada',
            'edu': 'United States',
            'ac.uk': 'United Kingdom',
            'edu.au': 'Australia'
        }
        
        extracted = tldextract.extract(url)
        suffix = extracted.suffix.lower()
        
        for domain, country in domain_countries.items():
            if domain in suffix:
                return country
                
        return ''

    def _extract_city(self, soup):
        """Extract city from content"""
        import re
        
        text = soup.get_text().lower()
        
        # Look for city patterns
        city_patterns = [
            r'located in ([a-z\s]+),',
            r'campus in ([a-z\s]+),',
            r'based in ([a-z\s]+),'
        ]
        
        for pattern in city_patterns:
            matches = re.findall(pattern, text)
            if matches:
                city = matches[0].strip().title()
                if len(city) > 2 and len(city) < 30:
                    return city
        
        return ''

    def _extract_domestic_fee(self, soup):
        """Extract domestic tuition fee"""
        patterns = [
            r'domestic.*?tuition.*?[\$CAD]*\s*([0-9,]+)',
            r'canadian.*?students.*?[\$CAD]*\s*([0-9,]+)',
            r'resident.*?fee.*?[\$CAD]*\s*([0-9,]+)'
        ]
        
        return self._extract_fee_by_patterns(soup, patterns)

    def _extract_international_fee(self, soup):
        """Extract international tuition fee"""
        patterns = [
            r'international.*?tuition.*?[\$CAD]*\s*([0-9,]+)',
            r'non-resident.*?fee.*?[\$CAD]*\s*([0-9,]+)',
            r'foreign.*?students.*?[\$CAD]*\s*([0-9,]+)'
        ]
        
        return self._extract_fee_by_patterns(soup, patterns)

    def _extract_application_fee(self, soup):
        """Extract application fee"""
        patterns = [
            r'application.*?fee.*?[\$CAD]*\s*([0-9,]+)',
            r'admission.*?fee.*?[\$CAD]*\s*([0-9,]+)'
        ]
        
        return self._extract_fee_by_patterns(soup, patterns)

    def _extract_deposit(self, soup):
        """Extract deposit amount"""
        patterns = [
            r'deposit.*?[\$CAD]*\s*([0-9,]+)',
            r'enrollment.*?deposit.*?[\$CAD]*\s*([0-9,]+)'
        ]
        
        return self._extract_fee_by_patterns(soup, patterns)

    def _extract_fee_by_patterns(self, soup, patterns):
        """Extract fee using regex patterns"""
        import re
        
        text = soup.get_text().lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    amount = float(matches[0].replace(',', ''))
                    if 100 <= amount <= 100000:
                        return f"{amount:.2f}"
                except ValueError:
                    continue
        
        return "0.00"

    def _extract_intakes(self, soup):
        """Extract intake periods"""
        text = soup.get_text().lower()
        intakes = []
        
        seasons = ['fall', 'spring', 'summer', 'winter', 'september', 'january', 'may']
        
        for season in seasons:
            if season in text:
                intakes.append({
                    'name': season.capitalize(),
                    'application_deadline': '',
                    'start_date': ''
                })
        
        return intakes[:4]

    def _extract_programs(self, soup):
        """Extract academic programs"""
        import re
        programs = []
        
        for element in soup.find_all(['a', 'li'], string=re.compile(r'bachelor|master|program', re.I)):
            text = element.get_text(strip=True)
            if 10 < len(text) < 100:
                programs.append({
                    'program_name': text,
                    'duration_years': 4 if 'bachelor' in text.lower() else 2
                })
        
        return programs[:10]

    def _extract_scholarships(self, soup):
        """Extract scholarship information"""
        scholarships = []
        
        for element in soup.find_all(['a', 'div'], string=re.compile(r'scholarship|grant|bursary', re.I)):
            text = element.get_text(strip=True)
            if 5 < len(text) < 100:
                scholarships.append({
                    'name': text,
                    'coverage': '',
                    'eligibility': ''
                })
        
        return scholarships[:5]

    def _extract_housing(self, soup):
        """Check if housing is available"""
        text = soup.get_text().lower()
        housing_keywords = ['residence', 'dormitory', 'housing', 'accommodation']
        
        return any(keyword in text for keyword in housing_keywords)

    def _extract_visa_info(self, soup):
        """Check if visa information is mentioned"""
        text = soup.get_text().lower()
        visa_keywords = ['visa', 'immigration', 'international students']
        
        return any(keyword in text for keyword in visa_keywords)

    def _find_fee_pages(self, soup, base_url):
        """Find links to tuition/fee pages"""
        fee_links = []
        
        # University-specific fee page patterns
        if 'utoronto.ca' in base_url:
            # Known UofT fee pages
            utoronto_fee_pages = [
                'https://www.utoronto.ca/admissions/tuition-fees',
                'https://future.utoronto.ca/finances/tuition-fees/',
                'https://www.utoronto.ca/admissions-awards/tuition-fees'
            ]
            fee_links.extend(utoronto_fee_pages)
        
        # General keyword search
        keywords = ['tuition', 'fees', 'cost', 'financial', 'money', 'admissions']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            if any(keyword in href or keyword in text for keyword in keywords):
                full_url = urljoin(base_url, link['href'])
                if full_url not in fee_links:
                    fee_links.append(full_url)
        
        return fee_links[:8]

    def _find_admission_pages(self, soup, base_url):
        """Find links to admission pages"""
        admission_links = []
        keywords = ['admission', 'apply', 'application', 'requirements']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            if any(keyword in href or keyword in text for keyword in keywords):
                full_url = urljoin(base_url, link['href'])
                if full_url not in admission_links:
                    admission_links.append(full_url)
        
        return admission_links[:5]

    def _extract_fees_from_pages(self, soups, fee_type):
        """Extract fees from multiple pages with enhanced patterns"""
        patterns = {
            'domestic': [
                r'domestic.*?(?:tuition|fee).*?\$?\s*([0-9,]+)',
                r'canadian.*?(?:citizen|student).*?\$?\s*([0-9,]+)',
                r'ontario.*?resident.*?\$?\s*([0-9,]+)',
                r'\$([0-9,]+).*?domestic',
                r'\$([0-9,]+).*?canadian'
            ],
            'international': [
                r'international.*?(?:tuition|fee).*?\$?\s*([0-9,]+)',
                r'non-resident.*?(?:tuition|fee).*?\$?\s*([0-9,]+)',
                r'foreign.*?student.*?\$?\s*([0-9,]+)',
                r'\$([0-9,]+).*?international',
                r'\$([0-9,]+).*?non-resident'
            ],
            'application': [
                r'application.*?fee.*?\$?\s*([0-9,]+)',
                r'admission.*?fee.*?\$?\s*([0-9,]+)',
                r'processing.*?fee.*?\$?\s*([0-9,]+)'
            ],
            'deposit': [
                r'deposit.*?\$?\s*([0-9,]+)',
                r'enrollment.*?deposit.*?\$?\s*([0-9,]+)',
                r'confirmation.*?deposit.*?\$?\s*([0-9,]+)'
            ]
        }
        
        for soup in soups:
            text = soup.get_text()
            # Look for fee tables and structured data
            for table in soup.find_all('table'):
                table_text = table.get_text().lower()
                for pattern in patterns.get(fee_type, []):
                    matches = re.findall(pattern, table_text, re.IGNORECASE | re.DOTALL)
                    if matches:
                        for match in matches:
                            try:
                                amount = float(str(match).replace(',', '').replace('$', ''))
                                if fee_type == 'application' and 50 <= amount <= 500:
                                    return f"{amount:.2f}"
                                elif fee_type in ['domestic', 'international'] and 5000 <= amount <= 80000:
                                    return f"{amount:.2f}"
                                elif fee_type == 'deposit' and 500 <= amount <= 10000:
                                    return f"{amount:.2f}"
                            except (ValueError, TypeError):
                                continue
            
            # General text search
            text_lower = text.lower()
            for pattern in patterns.get(fee_type, []):
                matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
                if matches:
                    for match in matches:
                        try:
                            amount = float(str(match).replace(',', '').replace('$', ''))
                            if fee_type == 'application' and 50 <= amount <= 500:
                                return f"{amount:.2f}"
                            elif fee_type in ['domestic', 'international'] and 5000 <= amount <= 80000:
                                return f"{amount:.2f}"
                            elif fee_type == 'deposit' and 500 <= amount <= 10000:
                                return f"{amount:.2f}"
                        except (ValueError, TypeError):
                            continue
        
        return "0.00"

    def _extract_intakes_from_pages(self, soups):
        """Extract intakes from multiple pages"""
        intakes = []
        seasons = ['fall', 'spring', 'summer', 'winter', 'september', 'january', 'may']
        
        for soup in soups:
            text = soup.get_text().lower()
            for season in seasons:
                if season in text and not any(i['name'] == season.capitalize() for i in intakes):
                    intakes.append({
                        'name': season.capitalize(),
                        'application_deadline': '',
                        'start_date': ''
                    })
        
        return intakes[:4]

    def _extract_programs_from_pages(self, soups):
        """Extract programs from multiple pages"""
        programs = []
        seen = set()
        
        for soup in soups:
            for element in soup.find_all(['a', 'li', 'h3'], string=re.compile(r'bachelor|master|program', re.I)):
                text = element.get_text(strip=True)
                if 10 < len(text) < 100 and text not in seen:
                    seen.add(text)
                    programs.append({
                        'program_name': text,
                        'duration_years': 4 if 'bachelor' in text.lower() else 2
                    })
        
        return programs[:10]

    def _extract_scholarships_from_pages(self, soups):
        """Extract scholarships from multiple pages"""
        scholarships = []
        seen = set()
        
        for soup in soups:
            for element in soup.find_all(['a', 'div'], string=re.compile(r'scholarship|grant|bursary', re.I)):
                text = element.get_text(strip=True)
                if 5 < len(text) < 100 and text not in seen:
                    seen.add(text)
                    scholarships.append({
                        'name': text,
                        'coverage': '',
                        'eligibility': ''
                    })
        
        return scholarships[:5]

    def _extract_housing_from_pages(self, soups):
        """Check housing from multiple pages"""
        housing_keywords = ['residence', 'dormitory', 'housing', 'accommodation']
        
        for soup in soups:
            text = soup.get_text().lower()
            if any(keyword in text for keyword in housing_keywords):
                return True
        
        return False

    def _extract_visa_from_pages(self, soups):
        """Check visa info from multiple pages"""
        visa_keywords = ['visa', 'immigration', 'international students']
        
        for soup in soups:
            text = soup.get_text().lower()
            if any(keyword in text for keyword in visa_keywords):
                return True
        
        return False