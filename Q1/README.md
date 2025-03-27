## Task

Get GitHub Repository statistics: 

Create a script that can get statistics from all the GitHub repositories of Kaggle
(https://github.com/Kaggle). Specifically, the script should generate a report (in a format that you
prefer) with the following information for all the repositories found under the Kaggle account.

- Total and median number of commits, stars, contributors, branches, tags, forks, releases,
closed issues, and environments (please use the GitHub’ API to perform this task).
    
- It should print out the total and median number of source code lines per programming
languages used from all the repositories of Kaggle (you are not allowed to use the GitHub
API for this part, but you may use any other tool or library).

## Implementation

- List of Programming Languages and corresponding file extensions are obtained from the YAML file extracted from the Github linguist project 
- Basic statistics are retrieved using the GitHub API.
- Line counts from each repository are retrieved using a web scraper. This allows us to avoid repeatedly cloning the repository, which may include large data files.
    - Scraper searches accesses each repository and accesses each file list.
    - Folders are recursively searched through until all files are found.
    - For file extensions that may be a programming language, the scraper accesses the file details page
    - File language and line count are scraped from the HTML
 
## Running the script

Use python3 git_repo_stats.py followed by a Github account name to run the file on a specific Github account (Ex: python3 git_repo_stats.py Kaggle
- if no account is specified, the program will default to using Kaggle
