## Task

Get GitHub Repository statistics: 

Create a script that can get statistics from all the GitHub repositories of Kaggle
(https://github.com/Kaggle). Specifically, the script should generate a report (in a format that you
prefer) with the following information for all the repositories found under the Kaggle account.
    • Total and median number of commits, stars, contributors, branches, tags, forks, releases,
    closed issues, and environments (please use the GitHub’ API to perform this task).
    
    • It should print out the total and median number of source code lines per programming
    languages used from all the repositories of Kaggle (you are not allowed to use the GitHub
    API for this part, but you may use any other tool or library).

## Implementation

- Basic statistics are retrieved using the GitHub API.
- Line counts from each repository are retrieved using a web scraper. This allows us to avoid repeatedly cloning the repository, which may include large data files.
    - Scraper searches accesses each repository and accesses each file list.
    - Folders are recursively searched through until all files are found.
    - File language is determined by the script within the web and line count is determined through the html