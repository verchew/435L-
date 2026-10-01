# =============================================================
# author: mary laro
# date: october 1, 2026
# assignment: week 4 - neo4j graph database integration
# course: sdc435l
# =============================================================

import json
from neo4j import GraphDatabase

# neo4j desktop local connection credentials
uri = "bolt://127.0.0.1:7687"
user = "neo4j"
password = "password1"

driver = GraphDatabase.driver(uri, auth=(user, password))

# -------------------------------------------------------------
# 1. data ingestion
# -------------------------------------------------------------
def load_data(limit=500):
    """loads commit records from json and creates user and repo nodes."""
    count = 0
    query = """
    MERGE (u:User {name: $author})
    MERGE (r:Repository {name: $repo})
    MERGE (u)-[c:COMMITTED_TO]->(r)
    ON CREATE SET c.count = 1
    ON MATCH SET c.count = c.count + 1
    """
    try:
        with open("Sample_Commits.json", "r", encoding="utf-8") as f:
            with driver.session() as session:
                for line in f:
                    if count >= limit:
                        break
                    line = line.strip()
                    if line:
                        item = json.loads(line)
                        repo = item.get("repo_name", "")
                        author_data = item.get("author", {})
                        author = author_data.get("name", "") if isinstance(author_data, dict) else str(author_data)

                        if repo and author:
                            session.run(query, author=author, repo=repo)
                            count += 1

        print(f"\n[success] ingested {count} commit relationships into neo4j.")
    except FileNotFoundError:
        print("\n[error] Sample_Commits.json not found in the current folder.")
    except Exception as e:
        print(f"\n[error] database connection failed: {e}")

# -------------------------------------------------------------
# 2. crud operations
# -------------------------------------------------------------
def create_repo():
    """create: insert a new repository node into the graph."""
    name = input("enter repository name (e.g., owner/repo): ").strip()
    if not name:
        print("[error] repository name cannot be empty.")
        return

    query = """
    MERGE (r:Repository {name: $name})
    ON CREATE SET r.created_at = timestamp()
    RETURN r.name AS repo_name
    """
    with driver.session() as session:
        result = session.run(query, name=name).single()
        print(f"[success] repository node '{result['repo_name']}' created or verified.")

def read_repo():
    """read: find a repository node and display its contributors."""
    name = input("enter repository name to view: ").strip()
    query = """
    MATCH (r:Repository {name: $name})
    OPTIONAL MATCH (u:User)-[c:COMMITTED_TO]->(r)
    RETURN r.name AS repo_name, collect(u.name) AS contributors
    """
    with driver.session() as session:
        result = session.run(query, name=name).single()
        if result and result["repo_name"]:
            print("\n--- repository details ---")
            print(f"name:         {result['repo_name']}")
            contributors = result["contributors"]
            print(f"contributors: {', '.join(contributors) if contributors else 'none recorded'}")
        else:
            print(f"[notice] repository '{name}' was not found.")

def update_repo():
    """update: rename an existing repository node."""
    old_name = input("enter current repository name: ").strip()
    new_name = input("enter new repository name: ").strip()
    if not old_name or not new_name:
        print("[error] names cannot be empty.")
        return

    query = """
    MATCH (r:Repository {name: $old_name})
    SET r.name = $new_name
    RETURN r.name AS updated_name
    """
    with driver.session() as session:
        result = session.run(query, old_name=old_name, new_name=new_name).single()
        if result:
            print(f"[success] updated repository name to '{result['updated_name']}'.")
        else:
            print(f"[notice] repository '{old_name}' was not found.")

def delete_repo():
    """delete: detach and delete a repository node and relationships."""
    name = input("enter repository name to delete: ").strip()
    query = """
    MATCH (r:Repository {name: $name})
    DETACH DELETE r
    RETURN count(r) AS deleted_count
    """
    with driver.session() as session:
        result = session.run(query, name=name).single()
        if result and result["deleted_count"] > 0:
            print(f"[success] repository '{name}' and attached relationships deleted.")
        else:
            print(f"[notice] repository '{name}' was not found.")

# -------------------------------------------------------------
# 3. analytical features
# -------------------------------------------------------------
def feature_collaboration_patterns():
    """feature 1: discover collaboration patterns between users sharing repositories."""
    query = """
    MATCH (u1:User)-[:COMMITTED_TO]->(r:Repository)<-[:COMMITTED_TO]-(u2:User)
    WHERE u1.name < u2.name
    RETURN u1.name AS user1, u2.name AS user2, count(r) AS shared_repos
    ORDER BY shared_repos DESC
    LIMIT 5
    """
    with driver.session() as session:
        results = list(session.run(query))
        print("\n--- collaboration patterns (users sharing repositories) ---")
        if not results:
            print("no shared repository collaborations found in current sample.")
            return
        for row in results:
            print(f"{row['user1']} & {row['user2']} -> {row['shared_repos']} shared repo(s)")

def feature_repo_similarities():
    """feature 2: find repository similarities based on common contributors."""
    query = """
    MATCH (r1:Repository)<-[:COMMITTED_TO]-(u:User)-[:COMMITTED_TO]->(r2:Repository)
    WHERE r1.name < r2.name
    RETURN r1.name AS repo1, r2.name AS repo2, count(u) AS common_contributors
    ORDER BY common_contributors DESC
    LIMIT 5
    """
    with driver.session() as session:
        results = list(session.run(query))
        print("\n--- repository similarities (common contributors) ---")
        if not results:
            print("no common contributors found across distinct repositories.")
            return
        for row in results:
            print(f"{row['repo1']} <-> {row['repo2']} -> {row['common_contributors']} common contributor(s)")

def feature_network_centrality():
    """feature 3: identify most active contributors and repositories by degree centrality."""
    user_query = """
    MATCH (u:User)-[c:COMMITTED_TO]->(:Repository)
    RETURN u.name AS user, count(c) AS repo_count
    ORDER BY repo_count DESC
    LIMIT 5
    """
    repo_query = """
    MATCH (:User)-[c:COMMITTED_TO]->(r:Repository)
    RETURN r.name AS repo, count(c) AS contributor_count
    ORDER BY contributor_count DESC
    LIMIT 5
    """
    with driver.session() as session:
        top_users = list(session.run(user_query))
        top_repos = list(session.run(repo_query))

        print("\n--- network centrality summary ---")
        print("top contributors (by repositories touched):")
        for u in top_users:
            print(f"  - {u['user']}: {u['repo_count']} repo(s)")

        print("\ntop repositories (by contributor count):")
        for r in top_repos:
            print(f"  - {r['repo']}: {r['contributor_count']} contributor(s)")

# -------------------------------------------------------------
# 4. main menu loop
# -------------------------------------------------------------
def main_menu():
    while True:
        print("\n==============================")
        print("   GitHub Archive - Neo4j CLI")
        print("==============================")
        print("1. Load Data from JSON")
        print("2. Create Repository Record")
        print("3. Read Repository Record")
        print("4. Update Repository Record")
        print("5. Delete Repository Record")
        print("6. [Feature 1] Collaboration Patterns")
        print("7. [Feature 2] Repository Similarities")
        print("8. [Feature 3] Network Centrality Summary")
        print("0. Exit")
        print("==============================")

        choice = input("select an option (0-8): ").strip()

        if choice == "1":
            load_data(limit=500)
        elif choice == "2":
            create_repo()
        elif choice == "3":
            read_repo()
        elif choice == "4":
            update_repo()
        elif choice == "5":
            delete_repo()
        elif choice == "6":
            feature_collaboration_patterns()
        elif choice == "7":
            feature_repo_similarities()
        elif choice == "8":
            feature_network_centrality()
        elif choice == "0":
            driver.close()
            print("\nexiting program. goodbye!")
            break
        else:
            print("\n[error] invalid selection. enter 0 through 8.")

if __name__ == "__main__":
    main_menu()
