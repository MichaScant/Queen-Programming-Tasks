import scrapy
import os
import yaml
import statistics
import logging
import pdb
import subprocess
import json
import requests
import tempfile
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

        #removes all the scrapy logging messages from the console
        logging.getLogger('scrapy').setLevel(logging.WARNING)
        logging.getLogger('urllib3').propagate = False
        logging.getLogger('chardet.charsetprober').setLevel(logging.INFO)

        self.github_account = kwargs.get('github_account')
        self.token = kwargs.get('token')

        self.valid_extensions = set()
        self.processed_languages_extensions_count = {}

        self.files_per_repo = {}

    # Starts the scraping process
    def start_requests(self):
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    
        # Load the list of programming file extensions from the GitHub Linguist language list
        with open('languages.yml') as f:
            languages = yaml.safe_load(f)

        for key, value in languages.items():
            if (value['type'] == 'programming' and 'extensions' in value):
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
        try:
            repository_data = response.css('script[data-target="react-app.embeddedData"]::text').get()
            repository_json_data = None
            file_list = None
            default_branch = None

            if not repository_data:
                scripts = response.css('script[data-target="react-partial.embeddedData"]::text').getall()
                for script in scripts:
                    if script:
                        repository_json_data = json.loads(script)
                        if 'initialPayload' in repository_json_data['props']:
                            file_list = repository_json_data['props']['initialPayload']['tree']['items']
                            default_branch = repository_json_data['props']['initialPayload']['repo']['defaultBranch']
                            break
            else:
                repository_json_data = json.loads(repository_data)
                file_list = repository_json_data['payload']['tree']['items']
                default_branch = repository_json_data['payload']['repo']['defaultBranch']
            
            if file_list:
                for file in file_list:
                    name = file['name']
                    if not name:
                        continue

                    base_repo_url = '/'.join(response.url.split('/')[:5])

                    if file['contentType'] == 'directory':
                        full_url = f"{base_repo_url}/tree/{default_branch}/{file['path']}"

                        yield scrapy.Request(url=full_url, callback=self.parse_repo, headers=self.headers)
                    else:
                        full_url = f"{base_repo_url}/blob/{default_branch}/{file['path']}"

                        filename, extension = os.path.splitext(name)

                        if not extension or extension.lower() in self.valid_extensions:
                            yield scrapy.Request(url=full_url, callback=self.parse_file_code, headers=self.headers)
                            
        except Exception as e:
            logging.error(f"Error parsing repository {response.url}: {str(e)}")

    # Parses the code from the file and gets the line count and language using cloc library
    def parse_file_code(self, response):
        try:
            source_file = response.url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            filename = source_file.split('/')[-1]  

            request_response = requests.get(source_file)
            source_file_text = request_response.text

            prefix, suffix = os.path.splitext(filename)

            #if the file has no extension, add the extension for detecting the language
            #as cloc relies on the extension to detect the file type
            if not suffix:
                suffix = f'.{filename.lower()}'

            # Download the source code into a temporary file and run CLOC to obtain the language and LOC count
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=True) as tmp_file:
                tmp_file.write(source_file_text)
                tmp_file.flush()

                analysis = subprocess.run(['cloc', '--json', tmp_file.name], capture_output=True, text=True, check=True).stdout

                analysis_json = json.loads(analysis)

            # Obtain the language and LOC count from the CLOC output
            if (analysis_json):
                #second key is the language type
                language = list(analysis_json.keys())[1]
                lines_of_source_code = analysis_json[language]['code']

                if language not in self.processed_languages_extensions_count:
                    self.processed_languages_extensions_count[language] = {'total': int(lines_of_source_code), 'values': [int(lines_of_source_code)]}
                else:
                    self.processed_languages_extensions_count[language]['total'] += int(lines_of_source_code)
                    self.processed_languages_extensions_count[language]['values'].append(int(lines_of_source_code))
        
        except Exception as e:
            logging.error(f"Error parsing file {response.url}: {str(e)}")

    def calculate_median(self, values):
        return statistics.median(values) 