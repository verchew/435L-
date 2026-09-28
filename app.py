import json
from cassandra.cluster import Cluster
from collections import Counter

# Connect to local Cassandra cluster
cluster = Cluster(['127.0.0.1'])
session = cluster.connect()

# Set up keyspace
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS github_keyspace 
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
""")
session.set_keyspace('github_keyspace')

# Table schema setup
session.execute("""
    CREATE TABLE IF NOT EXISTS repositories (
        repo_name text PRIMARY KEY,
        watch_count int
    );
""")

session.execute("""
    CREATE TABLE IF NOT EXISTS commits (
        commit_id text PRIMARY KEY,
        repo_name text,
        message text
    );
""")

# -------------------------------------------------------------
# 1. Data Ingestion
# -------------------------------------------------------------
def load_data(limit=1000):
    """Loads repository and commit data from JSON files."""
    repo_count = 0
    commit_count = 0

    # Ingest repositories
    try:
        with open("Sample_Repos.json", "r", encoding="utf-8") as f:
            for line in f:
                if repo_count >= limit:
                    break
                line = line.strip()
                if line:
                    item = json.loads(line)
                    name = item.get("repo_name", "")
                    try:
                        watch_count = int(item.get("watch_count", 0))
                    except ValueError:
                        watch_count = 0

                    if name:
                        session.execute(
                            "INSERT INTO repositories (repo_name, watch_count) VALUES (%s, %s);",
                            (name, watch_count)
                        )
                        repo_count += 1
        print(f"\n[Success] Loaded {repo_count} repositories into Cassandra.")
    except FileNotFoundError:
        print("\n[Error] Sample_Repos.json not found in current directory.")

    # Ingest commits
    try:
        with open("Sample_Commits.json", "r", encoding="utf-8") as f:
            for line in f:
                if commit_count >= limit:
                    break
                line = line.strip()
                if line:
                    item = json.loads(line)
                    c_id = item.get("commit", "")
                    repo = item.get("repo_name", "")
                    msg = item.get("message", "")
                    if c_id:
                        session.execute(
                            "INSERT INTO commits (commit_id, repo_name, message) VALUES (%s, %s, %s);",
                            (c_id, repo, msg)
                        )
                        commit_count += 1
        print(f"[Success] Loaded {commit_count} commits into Cassandra.")
    except FileNotFoundError:
        print("[Notice] Sample_Commits.json not found in current directory.")

# -------------------------------------------------------------
# 2. CRUD Operations
# -------------------------------------------------------------
def create_repo():
    """Create: Insert a new repository record."""
    name = input("Enter repository name (e.g., owner/repo): ").strip()
    if not name:
        print("[Error] Name cannot be empty.")
        return
    watch_input = input("Enter initial watch count: ").strip()
    watch_count = int(watch_input) if watch_input.isdigit() else 0

    session.execute(
        "INSERT INTO repositories (repo_name, watch_count) VALUES (%s, %s);",
        (name, watch_count)
    )
    print(f"[Success] Inserted repository '{name}'.")

def read_repo():
    """Read: Query a repository by name."""
    name = input("Enter repository name to view: ").strip()
    row = session.execute(
        "SELECT repo_name, watch_count FROM repositories WHERE repo_name = %s;",
        (name,)
    ).one()
    if row:
        print("\n--- Repository Details ---")
        print(f"Name:        {row.repo_name}")
        print(f"Watch Count: {row.watch_count}")
    else:
        print(f"[Notice] Repository '{name}' not found.")

def update_repo():
    """Update: Change the watch count for an existing repository."""
    name = input("Enter repository name to update: ").strip()
    row = session.execute(
        "SELECT repo_name FROM repositories WHERE repo_name = %s;",
        (name,)
    ).one()
    if not row:
        print(f"[Notice] Repository '{name}' not found.")
        return

    watch_input = input("Enter updated watch count: ").strip()
    if not watch_input.isdigit():
        print("[Error] Watch count must be an integer.")
        return

    session.execute(
        "UPDATE repositories SET watch_count = %s WHERE repo_name = %s;",
        (int(watch_input), name)
    )
    print(f"[Success] Updated '{name}'.")

def delete_repo():
    """Delete: Remove a repository record."""
    name = input("Enter repository name to delete: ").strip()
    session.execute(
        "DELETE FROM repositories WHERE repo_name = %s;",
        (name,)
    )
    print(f"[Success] Deleted repository '{name}' (if it existed).")

# -------------------------------------------------------------
# 3. Analytical Features
# -------------------------------------------------------------
def feature_trending_topics():
    """Feature 1: Identify trending topics/repositories by commit volume."""
    rows = session.execute("SELECT repo_name FROM commits;")
    counts = Counter(r.repo_name for r in rows if r.repo_name)

    if not counts:
        print("[Notice] No commit data available.")
        return

    print("\n--- Trending Topics: Most Active Repositories (Commit Count) ---")
    for rank, (repo, count) in enumerate(counts.most_common(5), start=1):
        print(f"{rank}. {repo} - {count} commits")

def feature_commit_message_words():
    """Feature 2: Popular words used in commit messages."""
    rows = session.execute("SELECT message FROM commits;")
    words = []
    stop_words = {"the", "a", "to", "and", "in", "of", "for", "on", "with", "is", "this", ""}

    for r in rows:
        if r.message:
            for token in r.message.lower().split():
                cleaned = "".join(c for c in token if c.isalnum())
                if cleaned and cleaned not in stop_words and len(cleaned) > 2:
                    words.append(cleaned)

    counts = Counter(words)
    if not counts:
        print("[Notice] No commit message tokens available.")
        return

    print("\n--- Most Frequent Words in Commit Messages ---")
    for rank, (word, count) in enumerate(counts.most_common(10), start=1):
        print(f"{rank}. '{word}' - {count} occurrences")

def feature_summary_metrics():
    """Feature 3: Dataset high-level summary metrics."""
    rows = session.execute("SELECT watch_count FROM repositories;")
    watches = [r.watch_count for r in rows if r.watch_count is not None]

    if not watches:
        print("[Notice] No repositories loaded.")
        return

    total_repos = len(watches)
    total_watches = sum(watches)
    avg_watches = total_watches / total_repos
    max_watches = max(watches)

    print("\n--- Repository Summary Metrics ---")
    print(f"Total Repositories: {total_repos}")
    print(f"Total Watches:      {total_watches}")
    print(f"Average Watches:    {avg_watches:.2f}")
    print(f"Maximum Watches:    {max_watches}")

# -------------------------------------------------------------
# 4. Main Menu Loop
# -------------------------------------------------------------
def main_menu():
    while True:
        print("\n==============================")
        print(" GitHub Archive - Cassandra CLI")
        print(" Marlar6882 Wk3 Project")
        print("==============================")
        print("1. Load Data from JSON")
        print("2. Create Repository Record")
        print("3. Read Repository Record")
        print("4. Update Repository Record")
        print("5. Delete Repository Record")
        print("6. [Feature 1] Trending Topics by Commits")
        print("7. [Feature 2] Popular Commit Words")
        print("8. [Feature 3] Summary Metrics")
        print("0. Exit")
        print("==============================")

        choice = input("Select an option (0-8): ").strip()

        if choice == "1":
            load_data(limit=1000)
        elif choice == "2":
            create_repo()
        elif choice == "3":
            read_repo()
        elif choice == "4":
            update_repo()
        elif choice == "5":
            delete_repo()
        elif choice == "6":
            feature_trending_topics()
        elif choice == "7":
            feature_commit_message_words()
        elif choice == "8":
            feature_summary_metrics()
        elif choice == "0":
            cluster.shutdown()
            print("\nExiting program. Goodbye!")
            break
        else:
            print("\n[Error] Invalid selection. Enter 0 through 8.")

if __name__ == "__main__":
    main_menu()
