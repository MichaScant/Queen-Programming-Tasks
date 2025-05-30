## Task

Crawl Issue Reports

I plan to study all issue reports filed against Apache Camel project. However, there is no
database available. Could you build a crawler to download a Jira issue report, parse it, and store
it into a .csv file? After you finish, please share with me the .csv file. Note that you are not
allowed to use the API for this task.

Example: You could crawl and parse the following issue report:
https://issues.apache.org/jira/browse/CAMEL-10597

Specifically, I want to get all properties of the issue CAMEL-10597
- “Details”, such as (Type: Bug),
- “People”, such as (Assignee: Claus Ibsen),
- “Dates”, such as (Created=1481726528/‘‘2016-12-14T14:42:08+0000’’, where 1481726528 is the epoch),
- “Description”, such as (‘‘Assume I have rest path ...’’),
- “Comments”, such as (ASF GitHub Bot:1481745300:14/Dec/16 14:55: ‘‘GitHub user bobpaulin opened a pull request: ...’’).

The example output is: Ln1 Type,...,Assignee,...,Created,Created Epoch,...,Description,Comments Ln2 Bug,...,Claus Ibsen,...,2016-12-14T14:42:08+0000,1481726528,...,Assume I have rest path ...,ASF GitHub Bot:1481745300:14/Dec/16 14:55:‘‘GitHub user bobpaulin opened a pull request: ...

## Implementation

- Web scraper is used to access the Jira issue report passed in as a command line argument.
- Scraper locates the export button and uses it to generate an XML version of the issue report.
- The XML is parsed and all information is stored in a .csv file.

## Running the script

Use python3 jira_crawler.py followed by a Jira issue url to run the file on a specific jira url (Ex: python3 jira_crawler.py https://issues.apache.org/jira/browse/CAMEL-10597)
- if no issue is specificed or a url is not passed in, the program will default to using the example provided in the Task
