from github import Github

import json

import scrapy

import os

import re

import pdb

import yaml

import statistics

from github import Auth

from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher

class GithubSpider(scrapy.Spider):
    name = 'github_spider'
    
    def __init__(self, *args, **kwargs):
        super(GithubSpider, self).__init__(*args, **kwargs)
        self.processed_languages_extensions = {}
        self.processed_languages_extensions_count = {}

    def start_requests(self):

        #TODO: remove the extension if come across a second time
        languages = yaml.safe_load(open('languages.yml'))
        for key, value in languages.items():
            if (value['type'] == 'programming' and 'extensions' in value):
                for extension in value['extensions']:
                    self.processed_languages_extensions[extension] = key
               
        url = "https://github.com/orgs/Kaggle/repositories"
        yield scrapy.Request(url=url, callback=self.parse_account)

    def parse_account(self, response):

        repo_list = response.css('ul.ListView-module__ul--vMLEZ')
        repo_items = repo_list.css('li')
        #print("Number of repositories: " + str(len(repo_items)))

        for repo in repo_items:
            url = f"https://github.com{repo.css('h3 a::attr(href)').get()}"
            yield scrapy.Request(url=url, callback=self.parse_repo)

    def parse_repo(self, response):
        file_list = response.css('table[aria-labelledby="folders-and-files"] tbody tr')
        for file in file_list:
            name = file.css('.react-directory-filename-column .react-directory-truncate a::text').get()
            full_url =  f"https://github.com{file.css('.react-directory-filename-column .react-directory-truncate a::attr(href)').get()}"

            is_directory = file.css('svg.octicon-file-directory-fill.icon-directory').get() is not None
            
            if is_directory:
                yield scrapy.Request(url=full_url, callback=self.parse_repo)
            else:
                if name is not None:
                    filename, extension = os.path.splitext(name)
                    if self.processed_languages_extensions.get(extension.lower()) is not None:
                        #if extension == '.tpl':
                         #   pdb.set_trace()
                        yield scrapy.Request(url=full_url, callback=self.parse_file, cb_kwargs={'extension': extension})

    def parse_file(self, response, extension):
        text = response.css('div.Box-sc-g0xbh4-0.bsDwxw.text-mono span::text').get()
        
        if text:
            matches = re.search(r'\((\d+)\s+loc\)', text)
            if matches:
                loc = matches.group(1)
                if extension not in self.processed_languages_extensions_count:
                    self.processed_languages_extensions_count[extension.lower()] = {'total': int(loc), 'values': [int(loc)]}
                else:
                    self.processed_languages_extensions_count[extension.lower()]['total'] += int(loc)
                    self.processed_languages_extensions_count[extension.lower()]['values'].append(int(loc))

    def calculate_median(self, values):
        return statistics.median(values)
        
def print_stastics(stats):
    for stat in stats:
        print(stat)

def get_statistics():
    auth = Auth.Token('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')
    
    g = Github(auth=auth)
    
    user = g.get_user("Kaggle")
    
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

    # Part 1
    
    stats = get_statistics()

    print_stastics(stats)

    # Part 2

    process = CrawlerProcess()
    
    def spider_closed(spider):
        print("Processing completed, here are the following results:")

        for extension, data in spider.processed_languages_extensions_count.items():
            median = 0
            if (data['total'] > 0):
                median = spider.calculate_median(data['values'])
            
            print(f"Language: {spider.processed_languages_extensions[extension]}, Median: {median}, Total: {data['total']}")
    
    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    process.crawl(GithubSpider)
    process.start()
    
if __name__ == "__main__":
    main()