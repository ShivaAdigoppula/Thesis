import json
import os
import time
from datetime import datetime


DATA_FILE = "users.json"
LOG_FILE = "app.log"


def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"[{timestamp}] {message}\n")


def load_users():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            write_log("Failed to read users.json")
            return []


def save_users(users):
    with open(DATA_FILE, "w") as file:
        json.dump(users, file, indent=2)


def create_user(username, password, role):
    users = load_users()

    for user in users:
        if user["username"] == username:
            print("User already exists")
            return False

    new_user = {
        "username": username,
        "password": password,
        "role": role,
        "created_at": datetime.now().isoformat()
    }

    users.append(new_user)
    save_users(users)
    write_log(f"Created user {username}")
    return True


def authenticate_user(username, password):
    users = load_users()

    for user in users:
        if user["username"] == username and user["password"] == password:
            write_log(f"Login success for {username}")
            return user

    write_log(f"Login failed for {username}")
    return None


def delete_user(username):
    users = load_users()
    updated_users = []

    for user in users:
        if user["username"] != username:
            updated_users.append(user)

    if len(updated_users) == len(users):
        print("User not found")
        return False

    save_users(updated_users)
    write_log(f"Deleted user {username}")
    return True


def list_users():
    users = load_users()

    if not users:
        print("No users found")
        return

    for user in users:
        print(f"Username: {user['username']}, Role: {user['role']}")


def search_user(keyword):
    users = load_users()
    results = []

    for user in users:
        if keyword.lower() in user["username"].lower():
            results.append(user)

    return results


def admin_report():
    users = load_users()
    total_users = len(users)
    admin_count = 0
    normal_count = 0

    for user in users:
        if user["role"] == "admin":
            admin_count += 1
        else:
            normal_count += 1

    report = {
        "total_users": total_users,
        "admin_users": admin_count,
        "normal_users": normal_count,
        "generated_at": datetime.now().isoformat()
    }

    print(json.dumps(report, indent=2))
    return report


def slow_backup():
    users = load_users()
    backup_name = f"backup_{int(time.time())}.json"

    time.sleep(2)

    with open(backup_name, "w") as file:
        json.dump(users, file, indent=2)

    write_log(f"Backup created: {backup_name}")
    return backup_name


def main():
    create_user("admin", "admin123", "admin")
    create_user("shiva", "password123", "user")
    create_user("testuser", "test123", "user")

    print("All users:")
    list_users()

    print("\nLogin test:")
    user = authenticate_user("admin", "admin123")

    if user:
        print("Login successful")
    else:
        print("Login failed")

    print("\nSearch result:")
    results = search_user("shi")

    for result in results:
        print(result)

    print("\nAdmin report:")
    admin_report()

    print("\nCreating backup:")
    backup_file = slow_backup()
    print(f"Backup saved as {backup_file}")


if __name__ == "__main__":
    main()
