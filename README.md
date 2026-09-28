# SDC435L - GitHub Archive Cassandra Application

A Python command-line application that ingests GitHub Archive data into an Apache Cassandra column-family database, performs CRUD operations, and provides dataset analysis.

---

## Technology Requirements & Dependencies

- **Operating System:** Ubuntu Linux / Windows 11
- **Python Version:** Python 3.8+
- **Database Engine:** Apache Cassandra (listening on default port 9042)
- **Python Libraries:**
  - `cassandra-driver`
  - `json` (Standard Library)
  - `collections.Counter` (Standard Library)

### Installing Dependencies

Run the following command in the terminal to install the Cassandra Python driver:

```bash
pip3 install cassandra-driver

Features Implemented
1. Data Ingestion

    Automatically initializes the keyspace github_keyspace with SimpleStrategy.

    Creates repositories and commits column-family tables with primary keys.

    Reads newline-delimited JSON records from Sample_Repos.json and Sample_Commits.json.

    Executes parameterized INSERT statements to populate both tables.

2. CRUD Operations

    Create: Inserts a repository record with name and watch count.

    Read: Queries and displays repository attributes by primary key (repo_name).

    Update: Updates the watch count for an existing repository record.

    Delete: Removes a repository record from the table.

3. Analytical Features

    Feature 1 (Trending Topics by Commit Volume): Queries commits, aggregates activity counts per repository, and displays the top 5 most active repositories.

    Feature 2 (Popular Commit Message Words): Extracts messages from the commits table, removes stop words, and displays the top 10 most frequent words.

    Feature 3 (Repository Summary Metrics): Queries watch counts to calculate and display total repositories, total watches, average watches, and maximum watch count.
