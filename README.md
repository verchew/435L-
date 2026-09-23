# SDC435L - GitHub Archive Redis Application

A Python application that ingests GitHub Archive JSON data, stores records in a Redis database, and provides an interactive command-line interface (CLI) to perform full CRUD operations and analytical reporting.

---

## Technology Requirements & Dependencies

- **Operating System:** Ubuntu Linux / Windows 10/11
- **Python Version:** Python 3.8+ (tested on Python 3.8 / IDLE)
- **Database Engine:** Redis Server 6.x or higher (listening on port 6379)
- **Python Libraries:**
  - `redis` (Python client for Redis)
  - `json` (Standard Library)

### Installing Dependencies

Run the following command in your terminal to install the necessary Python Redis library:

```bash
pip3 install redis

sudo service redis-server start

Project/
├── app.py
├── README.md
└── data/
    └── Sample_Repos.json

python3 app.py

Current Features & CRUD Capabilities
1. Data Ingestion
Reads newline-delimited JSON (NDJSON) from data/Sample_Repos.json.

Utilizes Redis pipelines for efficient batch ingestion.

Stores repository data using Redis Hashes (repo:<repo_name>) and indexes repository keys in a Redis Set (all_repos).

2. Interactive CRUD Operations
Create: Adds a new repository record to the database with a user-specified name and initial watch count.

Read: Looks up and displays the detailed watch metrics for any specific repository name.

Update: Updates the watch count for an existing repository record.

Delete: Removes the repository hash from Redis and deregisters it from the global tracking set.

3. Analytical Features
Feature 1 (Top 5 Most-Watched Repositories): Scans existing repository records and outputs the top 5 most-watched projects sorted in descending order.

Feature 2 (Database Metrics & Statistics): Computes and displays overall dataset statistics, including total repositories stored, total watch count across all records, average watches per repository, and highest single watch count.

Feature 3 (Search by Owner / Organization): Allows users to search by organization or username prefix (e.g., FreeCodeCamp, google) and lists all matching repositories stored in the database.
