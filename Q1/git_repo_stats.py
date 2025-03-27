import os
import sys

from github import Github
from github import Auth

from dotenv import load_dotenv

from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher

from github_spider import GithubSpider

# Load environment variables from .env file
load_dotenv()

def print_stastics(stats):
    for stat in stats:
        print(stat)

def get_statistics(github_account, token):
    if not token:
        raise EnvironmentError("GITHUB_TOKEN environment variable is not set. Please set it with your GitHub Personal Access Token.")
    
    auth = Auth.Token(token)
    
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

    token = os.environ.get('GITHUB_TOKEN')

    # Part 1
    
    stats = get_statistics(github_account, token)

    print_stastics(stats)

    # Part 2

    process = CrawlerProcess()
    
    def spider_closed(spider):
        print("Processing completed, results:")

        for title, data in spider.processed_languages_extensions_count.items():
            median = 0
            if (data['total'] > 0):
                median = spider.calculate_median(data['values'])
            
            print(f"Language: {title}, Median: {median}, Total: {data['total']}")
    
    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    process.crawl(GithubSpider, github_account=github_account, token=token)
    process.start()
    
if __name__ == "__main__":
    main()