import scrapy
import os
import re
import yaml
import statistics
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

'''
Scraper for GitHub repositories

finds the total and median line counts for each programming language across all the repositories on the account
'''
class GithubSpider(scrapy.Spider):
    name = 'github_spider'
    
    def __init__(self, *args, **kwargs):
        super(GithubSpider, self).__init__(*args, **kwargs)
        logging.getLogger('scrapy').setLevel(logging.WARNING)
        
        self.github_account = kwargs.get('github_account')
        self.token = kwargs.get('token')

        self.valid_language_names = set()
        self.valid_extensions = set()
        self.processed_languages_extensions_count = {}

        self.files_per_repo = {}

    # Starts the scraping process
    def start_requests(self):
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    
        with open('languages.yml') as f:
            languages = yaml.safe_load(f)

        for key, value in languages.items():
            if (value['type'] == 'programming' and 'extensions' in value):
                self.valid_language_names.add(key)
                
                for extension in value['extensions']:
                    self.valid_extensions.add(extension)

                url = f"https://github.com/orgs/{self.github_account}/repositories"
                yield scrapy.Request(
                    url=url, callback=self.parse_account, headers=self.headers)

    # Parses the account page and accesses each repository
    def parse_account(self, response):
        repo_list = response.css('ul.ListView-module__ul--vMLEZ')
        repo_items = repo_list.css('li')
        for repo in repo_items:
            url = f"https://github.com{repo.css('h3 a::attr(href)').get()}"
            yield scrapy.Request(url=url, callback=self.parse_repo, headers=self.headers)

    # Parses the repository page and accesses each file, recursively accessing directories
    def parse_repo(self, response):
        file_list = response.css('table[aria-labelledby="folders-and-files"] tbody tr')
        for file in file_list:
            name = file.css('.react-directory-filename-column .react-directory-truncate a::text').get()
            full_url =  f"https://github.com{file.css('.react-directory-filename-column .react-directory-truncate a::attr(href)').get()}"

            is_directory = file.css('svg.octicon-file-directory-fill.icon-directory').get() is not None
            
            if is_directory:
                yield scrapy.Request(url=full_url, callback=self.parse_repo, headers=self.headers)
            else:
                if name is not None:
                    filename, extension = os.path.splitext(name)

                    if not extension or extension.lower() in self.valid_extensions:
                        yield scrapy.Request(url=full_url, callback=self.parse_file, cb_kwargs={'filename': filename}, headers=self.headers)

    # Parses the file page and gets the line count and language
    def parse_file(self, response, filename):
        text = response.css('div.Box-sc-g0xbh4-0.bsDwxw.text-mono div[data-testid="blob-size"] span::text').get()
        if text:
            matches = re.search(r'\((\d+)\s+loc\)', text)
            if matches:
                loc = matches.group(1)

                script = response.css('script[data-target="react-app.embeddedData"]::text').get()

                lang_marker = '"language":"'
                start = script.find(lang_marker) + len(lang_marker)
                end = script.find('"', start)
                
                language = script[start:end]

                if language in self.valid_language_names:
                    if language not in self.processed_languages_extensions_count:
                        self.processed_languages_extensions_count[language] = {'total': int(loc), 'values': [int(loc)]}
                    else:
                        self.processed_languages_extensions_count[language]['total'] += int(loc)
                        self.processed_languages_extensions_count[language]['values'].append(int(loc))

    def calculate_median(self, values):
        return statistics.median(values) 