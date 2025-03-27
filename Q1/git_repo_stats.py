from github import Github

import json

import scrapy

import os

import sys

import re

import yaml

import statistics

from github import Auth

from dotenv import load_dotenv

from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher

# Load environment variables from .env file
load_dotenv()

TOKEN = os.environ.get('GITHUB_TOKEN')

class GithubSpider(scrapy.Spider):
    
    name = 'github_spider'
    
    def __init__(self, *args, **kwargs):
        super(GithubSpider, self).__init__(*args, **kwargs)
        
        self.github_account = kwargs.get('github_account')
        
        self.valid_language_names = set()
        self.valid_extensions = set()
        self.processed_languages_extensions_count = {}

        self.files_per_repo = {}

    def start_requests(self):
        self.headers = {
            'Authorization': f'token {TOKEN}',
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

    def parse_account(self, response):
        repo_list = response.css('ul.ListView-module__ul--vMLEZ')
        repo_items = repo_list.css('li')
        print("repo_items", len(repo_items))
        for repo in repo_items:
            url = f"https://github.com{repo.css('h3 a::attr(href)').get()}"
            yield scrapy.Request(url=url, callback=self.parse_repo, headers=self.headers)

    def parse_repo(self, response):
        '''url_parts = response.url.split('/')
        org_index = url_parts.index(self.github_account)
        if len(url_parts) > org_index + 1:
            repo_name = url_parts[org_index + 1]
        
        # Only initialize the counter if this is a new repository (not a subdirectory)
        if repo_name not in self.files_per_repo and 'tree' not in url_parts:
            self.files_per_repo[repo_name] = 0'''

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
                    #self.files_per_repo[repo_name] += 1
                    if language not in self.processed_languages_extensions_count:
                        self.processed_languages_extensions_count[language] = {'total': int(loc), 'values': [int(loc)]}
                    else:
                        self.processed_languages_extensions_count[language]['total'] += int(loc)
                        self.processed_languages_extensions_count[language]['values'].append(int(loc))

    def calculate_median(self, values):
        return statistics.median(values)
        
def print_stastics(stats):
    for stat in stats:
        print(stat)

def get_statistics(github_account):
    if not TOKEN:
        raise EnvironmentError("GITHUB_TOKEN environment variable is not set. Please set it with your GitHub Personal Access Token.")
    
    auth = Auth.Token(TOKEN)
    
    g = Github(auth=auth)
    
    user = g.get_user(github_account)
    
    repos_info = []
    
    for repo in user.get_repos():
        repos_info.append({
            "name": repo.name,
            "commits": repo.get_commits().totalCount,
            "stars": repo.stargazers_count,
            "contributors": repo.get_contributors().totalCount,
            "branches": repo.get_branches().totalCount,
            "forks": repo.forks_count,
            "releases": repo.get_releases().totalCount,
            "closed_issues": repo.get_issues(state='closed').totalCount,
            "environments": repo.get_environments().totalCount
        })

    return repos_info

def main():
    #argument parser
    github_account = 'Kaggle'
    
    if len(sys.argv) != 1:
        github_account = sys.argv[1]

    # Part 1
    
    #stats = get_statistics(github_account)

    #print_stastics(stats)

    # Part 2

    process = CrawlerProcess()
    
    def spider_closed(spider):
        print("Processing completed, here are the following results:")

        print("File counts per repository:")
        for repo_name, file_count in spider.files_per_repo.items():
            print(f"Repository: {repo_name}, File count: {file_count}")

        for title, data in spider.processed_languages_extensions_count.items():

            median = 0
            if (data['total'] > 0):
                median = spider.calculate_median(data['values'])
            
            print(f"Language: {title}, Median: {median}, Total: {data['total']}")
    
    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    process.crawl(GithubSpider, github_account=github_account)
    process.start()
    
if __name__ == "__main__":
    main()