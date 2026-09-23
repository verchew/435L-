import json
import redis

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# -------------------------------------------------------------
# 1. Data Ingestion
# -------------------------------------------------------------
def load_data(limit=1000):
    """Loads records from Sample_Repos.json into Redis using pipelining."""
    count = 0
    try:
        with open("data/Sample_Repos.json", "r", encoding="utf-8") as f:
            pipe = r.pipeline()
            for line in f:
                if count >= limit:
                    break
                line = line.strip()
                if line:
                    item = json.loads(line)
                    name = item.get("repo_name")
                    watch_count = item.get("watch_count", "0")
                    
                    key = f"repo:{name}"
                    pipe.hset(key, mapping={"repo_name": name, "watch_count": str(watch_count)})
                    pipe.sadd("all_repos", name)
                    count += 1
            pipe.execute()
        print(f"\n[Success] Loaded {count} repositories into Redis.")
    except FileNotFoundError:
        print("\n[Error] data/Sample_Repos.json not found. Check your file path.")

# -------------------------------------------------------------
# 2. CRUD Operations
# -------------------------------------------------------------
def create_repo():
    """Create: Add a new repository."""
    name = input("Enter repository name (e.g., owner/repo): ").strip()
    if not name:
        print("[Error] Repository name cannot be empty.")
        return
    
    key = f"repo:{name}"
    if r.exists(key):
        print(f"[Notice] Repository '{name}' already exists.")
        return
    
    watch_count = input("Enter initial watch count: ").strip()
    if not watch_count.isdigit():
        watch_count = "0"
        
    r.hset(key, mapping={"repo_name": name, "watch_count": watch_count})
    r.sadd("all_repos", name)
    print(f"[Success] Repository '{name}' added with {watch_count} watches.")

def read_repo():
    """Read: Search and display a repository by name."""
    name = input("Enter repository name to view: ").strip()
    key = f"repo:{name}"
    data = r.hgetall(key)
    if data:
        print(f"\n--- Repository Details ---")
        print(f"Name:        {data.get('repo_name')}")
        print(f"Watch Count: {data.get('watch_count')}")
    else:
        print(f"[Notice] Repository '{name}' was not found.")

def update_repo():
    """Update: Modify watch count for an existing repository."""
    name = input("Enter repository name to update: ").strip()
    key = f"repo:{name}"
    if not r.exists(key):
        print(f"[Notice] Repository '{name}' was not found.")
        return
    
    new_count = input("Enter new watch count: ").strip()
    if not new_count.isdigit():
        print("[Error] Watch count must be a number.")
        return
        
    r.hset(key, "watch_count", new_count)
    print(f"[Success] Updated '{name}' watch count to {new_count}.")

def delete_repo():
    """Delete: Remove a repository record."""
    name = input("Enter repository name to delete: ").strip()
    key = f"repo:{name}"
    if r.delete(key):
        r.srem("all_repos", name)
        print(f"[Success] Repository '{name}' deleted.")
    else:
        print(f"[Notice] Repository '{name}' was not found.")

# -------------------------------------------------------------
# 3. Analytical Features
# -------------------------------------------------------------
def feature_top_watched(top_n=5):
    """Feature 1: Find and rank the most-watched repositories."""
    repo_names = r.smembers("all_repos")
    if not repo_names:
        print("[Notice] Database is empty. Load data first.")
        return

    pipe = r.pipeline()
    names_list = list(repo_names)
    for name in names_list:
        pipe.hget(f"repo:{name}", "watch_count")
    counts = pipe.execute()

    # Pair records and sort numerically descending
    records = []
    for name, count in zip(names_list, counts):
        val = int(count) if count and count.isdigit() else 0
        records.append((name, val))
    
    records.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n--- Top {top_n} Most Watched Repositories ---")
    for rank, (name, count) in enumerate(records[:top_n], start=1):
        print(f"{rank}. {name} - {count:,} watches")

def feature_summary_statistics():
    """Feature 2: Compute repository count and watch metrics."""
    repo_names = r.smembers("all_repos")
    total_repos = len(repo_names)
    if total_repos == 0:
        print("[Notice] Database is empty. Load data first.")
        return

    pipe = r.pipeline()
    for name in repo_names:
        pipe.hget(f"repo:{name}", "watch_count")
    counts = [int(c) for c in pipe.execute() if c and c.isdigit()]

    total_watches = sum(counts)
    avg_watches = total_watches / total_repos if total_repos else 0
    max_watches = max(counts) if counts else 0

    print("\n--- Dataset Summary Statistics ---")
    print(f"Total Repositories: {total_repos:,}")
    print(f"Total Watch Count:  {total_watches:,}")
    print(f"Average Watches:    {avg_watches:.2f}")
    print(f"Highest Watch Count:{max_watches:,}")

def feature_search_by_owner():
    """Feature 3: Filter repositories by owner or organization name."""
    owner = input("Enter owner/user name to search (e.g., FreeCodeCamp): ").strip().lower()
    if not owner:
        return
    
    repo_names = r.smembers("all_repos")
    matches = [name for name in repo_names if name.lower().startswith(f"{owner}/")]

    print(f"\n--- Repositories owned by '{owner}' ({len(matches)} found) ---")
    if matches:
        for name in matches[:10]:
            count = r.hget(f"repo:{name}", "watch_count")
            print(f"- {name} ({count} watches)")
        if len(matches) > 10:
            print(f"...and {len(matches) - 10} more.")
    else:
        print("No matching repositories found.")

# -------------------------------------------------------------
# 4. Main Menu Loop
# -------------------------------------------------------------
def main_menu():
    while True:
        print("\n==============================")
        print(" GitHub Archive - Redis CLI")
        print("==============================")
        print("1. Load / Refresh Data from JSON")
        print("2. Create Repository Record")
        print("3. Read Repository Record")
        print("4. Update Repository Record")
        print("5. Delete Repository Record")
        print("6. [Feature 1] Top 5 Most-Watched Repos")
        print("7. [Feature 2] Database Statistics")
        print("8. [Feature 3] Search by Owner/Org")
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
            feature_top_watched(top_n=5)
        elif choice == "7":
            feature_summary_statistics()
        elif choice == "8":
            feature_search_by_owner()
        elif choice == "0":
            print("\nExiting program. Goodbye!")
            break
        else:
            print("\n[Error] Invalid selection. Please enter 0 through 8.")

if __name__ == "__main__":
    main_menu()
