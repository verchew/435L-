# SDC435L - GitHub Archive Neo4j Application

A Python command-line application that ingests GitHub Archive commit data into an open-source Neo4j graph database, performs CRUD operations on graph nodes, and runs Cypher analytical queries.

---

## Technology Requirements & Dependencies

- **Operating System:** Windows 11 / Ubuntu Linux
- **Python Version:** Python 3.8+ (tested on Python 3.14)
- **Database Engine:** Neo4j Desktop / Community Server (Bolt protocol on port 7687)
- **Python Libraries:**
  - `neo4j`
  - `json` (Standard Library)

### Installing Dependencies

Run the following command in Command Prompt:

```cmd
py -m pip install neo4j
