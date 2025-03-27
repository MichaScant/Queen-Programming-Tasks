import re
import os
import xml.etree.ElementTree as ET
import csv
import sys
from bs4 import BeautifulSoup
from datetime import datetime
import validators

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher

TOKEN = os.environ.get('GITHUB_TOKEN')

class GithubSpider(scrapy.Spider):
    name = 'github_spider'
    
    def __init__(self, *args, **kwargs):
        super(GithubSpider, self).__init__(*args, **kwargs)
        self.url = kwargs.get('url')

    def start_requests(self):
        self.headers = {
            'Authorization': f'token {TOKEN}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
            
        yield scrapy.Request(url=self.url, callback=self.parse_report, headers=self.headers)

    def parse_report(self, response):
        # Find the XML export link
        xml_link = response.css('aui-item-link[id="jira.issueviews:issue-xml"]::attr(href)').get()

        yield scrapy.Request(url=f"https://issues.apache.org" + xml_link, callback=self.parse_xml, headers=self.headers)
    
    def parse_xml(self, response):
        root = ET.fromstring(response.body)

        data = {}
        
        #finding details of the issue
        type = root.find('.//type').text.strip() or "None"
        data['Type'] = type

        priority = root.find('.//priority').text.strip() or "None"
        data['Priority'] = priority

        status = root.find('.//status').text.strip() or "None"
        data['Status'] = status

        resolution = root.find('.//resolution').text.strip() or "None"
        data['Resolution'] = resolution

        affected_version = root.find('.//item/version').text.strip() or "None"
        data['Affected Version'] = affected_version

        fix_versions = root.findall('.//fixVersion')
        data['Fix Versions'] = ', '.join([version.text.strip() for version in fix_versions])

        components = root.find('.//component').text.strip() or "None"
        data['Components'] = components

        labels = root.find('.//labels').text.strip() or "None"
        data['Labels'] = labels

        patch_info = root.find('.//customfield[@id="customfield_12310041"]//customfieldvalue').text.strip() or "None"
        data['Patch Info'] = patch_info

        estimated_complexity = root.find('.//customfield[@id="customfield_12310060"]//customfieldvalue').text.strip() or "None"
        data['Estimated Complexity'] = estimated_complexity

        #finding people

        assignee = root.find('.//assignee').text.strip() or "None"
        data['Assignee'] = assignee

        reporter = root.find('.//reporter').text.strip() or "None"
        data['Reporter'] = reporter

        #finding dates
        created_date = root.find('.//created').text.strip() or "None"
        data['Created Date'] = self.format_date(created_date)

        updated_date = root.find('.//updated').text.strip() or "None"
        data['Updated Date'] = self.format_date(updated_date)

        resolution_date = root.find('.//resolved').text.strip() or "None"
        data['Resolution Date'] = self.format_date(resolution_date)
        
        #finding description
        description = root.find('.//item/description').text.strip() or "None"
        data['Description'] = self.clean_html_tags(description)

        #finding comments
        comments = root.findall('.//comment')
        comments_list = []
        
        for comment in comments:
            author = comment.get('author', 'Unknown')
            created = comment.get('created', 'Unknown date')
            comment_text = comment.text.strip() if comment.text else "No comment text"
            clean_comment = self.clean_html_tags(comment_text)

            formatted_date = self.format_date(created)

            formatted_comment = f"{author}:{formatted_date}: ''{clean_comment}''"
            comments_list.append(formatted_comment)

        data['Comments'] = '\n\n\n'.join(comments_list)
        
        #parse to csv
        with open('jira_issue_information.csv', 'w', newline='') as csvfile:
            
            fieldnames = ['Type', 'Priority', 'Status', 'Resolution', 'Affected Version', 
                          'Fix Versions', 'Components', 'Labels', 'Patch Info', 
                          'Estimated Complexity', 'Assignee', 'Reporter', 'Created Date', 
                          'Updated Date', 'Resolution Date', 'Description', 'Comments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(data)

    def clean_html_tags(self, html_text):
        text = BeautifulSoup(html_text, "html.parser").get_text(separator="\n")
        return re.sub(r'\n+', '\n', text).strip()
    
    def format_date(self, date_string):
        date_obj = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        formatted_date = date_obj.strftime("%d/%b/%y %H:%M")
        unix_timestamp = int(date_obj.timestamp())
        return f"{unix_timestamp}:{formatted_date}"

def main():

    url = "https://issues.apache.org/jira/browse/CAMEL-10597"
    
    if len(sys.argv) != 1:
        if validators.url(sys.argv[1]):
            url = sys.argv[1]
        
    process = CrawlerProcess()
    
    def spider_closed(spider):
        print("Processing completed, here are the following results:")

    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    process.crawl(GithubSpider, url=url)
    process.start()
    
if __name__ == "__main__":
    main()