import json
from pymongo import MongoClient

# connect to local mongodb
client = MongoClient("mongodb://localhost:27017/")
db = client["github_db"]
repos_col = db["repositories"]

# -------------------------------------------------------------
# 1. data ingestion
# -------------------------------------------------------------
def load_data(limit=1000):
    """loads records from Sample_Repos.json into mongodb."""
    records = []
    count = 0
    try:
        # direct path to the file in the same folder
        with open("Sample_Repos.json", "r", encoding="utf-8") as f:
            for line in f:
                if count >= limit:
                    break
                line = line.strip()
                if line:
                    item = json.loads(line)
                    raw_count = item.get("watch_count", 0)
                    try:
                        watch_count = int(raw_count)
                    except ValueError:
                        watch_count = 0

                    doc = {
                        "repo_name": item.get("repo_name"),
                        "watch_count": watch_count
                    }
                    records.append(doc)
                    count += 1

        if records:
            repos_col.delete_many({})
            repos_col.insert_many(records)
            print(f"\n[success] loaded {len(records)} repositories into mongodb.")
    except FileNotFoundError:
        print("\n[error] Sample_Repos.json not found in the current folder.")

# -------------------------------------------------------------
# 2. crud operations
# -------------------------------------------------------------
def create_repo():
    """create: insert a new repository document."""
    name = input("enter repository name (e.g., owner/repo): ").strip()
    if not name:
        print("[error] repository name cannot be empty.")
        return

    if repos_col.find_one({"repo_name": name}):
        print(f"[notice] repository '{name}' already exists.")
        return

    watch_input = input("enter initial watch count: ").strip()
    watch_count = int(watch_input) if watch_input.isdigit() else 0

    new_doc = {"repo_name": name, "watch_count": watch_count}
    repos_col.insert_one(new_doc)
    print(f"[success] created repository '{name}'.")

def read_repo():
    """read: find and display a repository document."""
    name = input("enter repository name to view: ").strip()
    doc = repos_col.find_one({"repo_name": name})
    if doc:
        print("\n--- repository details ---")
        print(f"name:        {doc.get('repo_name')}")
        print(f"watch count: {doc.get('watch_count')}")
    else:
        print(f"[notice] repository '{name}' was not found.")

def update_repo():
    """update: modify watch count for an existing repository."""
    name = input("enter repository name to update: ").strip()
    doc = repos_col.find_one({"repo_name": name})
    if not doc:
        print(f"[notice] repository '{name}' was not found.")
        return

    watch_input = input("enter new watch count: ").strip()
    if not watch_input.isdigit():
        print("[error] watch count must be a number.")
        return

    new_count = int(watch_input)
    repos_col.update_one({"repo_name": name}, {"$set": {"watch_count": new_count}})
    print(f"[success] updated '{name}' watch count to {new_count}.")

def delete_repo():
    """delete: remove a repository document."""
    name = input("enter repository name to delete: ").strip()
    result = repos_col.delete_one({"repo_name": name})
    if result.deleted_count > 0:
        print(f"[success] repository '{name}' deleted.")
    else:
        print(f"[notice] repository '{name}' was not found.")

# -------------------------------------------------------------
# 3. analytical features
# -------------------------------------------------------------
def feature_longest_shortest_names():
    """feature 1: survey of the longest and shortest repository names."""
    total = repos_col.count_documents({})
    if total == 0:
        print("[notice] database is empty. load data first.")
        return

    pipeline = [
        {"$project": {"repo_name": 1, "name_length": {"$strLenCP": "$repo_name"}}},
        {"$sort": {"name_length": -1}}
    ]
    results = list(repos_col.aggregate(pipeline))

    longest = results[0]
    shortest = results[-1]

    print("\n--- repository name length survey ---")
    print(f"longest name ({longest['name_length']} chars):  {longest['repo_name']}")
    print(f"shortest name ({shortest['name_length']} chars): {shortest['repo_name']}")

def feature_watch_distribution():
    """feature 2: distribution of repositories by watch count tier."""
    total = repos_col.count_documents({})
    if total == 0:
        print("[notice] database is empty. load data first.")
        return

    tier_0_10 = repos_col.count_documents({"watch_count": {"$lte": 10}})
    tier_11_100 = repos_col.count_documents({"watch_count": {"$gt": 10, "$lte": 100}})
    tier_101_1000 = repos_col.count_documents({"watch_count": {"$gt": 100, "$lte": 1000}})
    tier_1000_plus = repos_col.count_documents({"watch_count": {"$gt": 1000}})

    print("\n--- watch count distribution ---")
    print(f"0 - 10 watches:      {tier_0_10} repositories")
    print(f"11 - 100 watches:    {tier_11_100} repositories")
    print(f"101 - 1,000 watches: {tier_101_1000} repositories")
    print(f"1,001+ watches:      {tier_1000_plus} repositories")

def feature_top_watched(top_n=5):
    """feature 3: top most-watched repositories."""
    total = repos_col.count_documents({})
    if total == 0:
        print("[notice] database is empty. load data first.")
        return

    top_cursor = repos_col.find().sort("watch_count", -1).limit(top_n)

    print(f"\n--- top {top_n} most watched repositories ---")
    for rank, doc in enumerate(top_cursor, start=1):
        print(f"{rank}. {doc.get('repo_name')} - {doc.get('watch_count'):,} watches")

# -------------------------------------------------------------
# 4. main menu loop
# -------------------------------------------------------------
def main_menu():
    while True:
        print("\n==============================")
        print(" GitHub Archive - MongoDB CLI")
        print("==============================")
        print("1. Load Data from JSON")
        print("2. Create Repository Record")
        print("3. Read Repository Record")
        print("4. Update Repository Record")
        print("5. Delete Repository Record")
        print("6. [Feature 1] Longest & Shortest Names")
        print("7. [Feature 2] Watch Count Distribution")
        print("8. [Feature 3] Top 5 Most-Watched")
        print("0. Exit")
        print("==============================")

        choice = input("select an option (0-8): ").strip()

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
            feature_longest_shortest_names()
        elif choice == "7":
            feature_watch_distribution()
        elif choice == "8":
            feature_top_watched(top_n=5)
        elif choice == "0":
            print("\nexiting program. goodbye!")
            break
        else:
            print("\n[error] invalid selection. please enter 0 through 8.")

if __name__ == "__main__":
    main_menu()
