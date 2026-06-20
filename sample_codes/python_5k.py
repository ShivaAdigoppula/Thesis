import json
import csv
import os
import time
from datetime import datetime


DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
ENROLLMENTS_FILE = os.path.join(DATA_DIR, "enrollments.json")
GRADES_FILE = os.path.join(DATA_DIR, "grades.json")
LOG_FILE = os.path.join(DATA_DIR, "application.log")


def ensure_data_directory():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def write_log(message):
    ensure_data_directory()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def read_json_file(file_path):
    ensure_data_directory()

    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        write_log(f"JSON decode error in file: {file_path}")
        return []
    except Exception as error:
        write_log(f"Unexpected error while reading {file_path}: {error}")
        return []


def write_json_file(file_path, data):
    ensure_data_directory()

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        return True
    except Exception as error:
        write_log(f"Failed to write file {file_path}: {error}")
        return False


def generate_id(prefix):
    current_time = int(time.time() * 1000)
    return f"{prefix}_{current_time}"


def create_user(username, password, full_name, email, role):
    users = read_json_file(USERS_FILE)

    for user in users:
        if user["username"] == username:
            print("Username already exists")
            write_log(f"User creation failed. Duplicate username: {username}")
            return None

    user = {
        "user_id": generate_id("user"),
        "username": username,
        "password": password,
        "full_name": full_name,
        "email": email,
        "role": role,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

    users.append(user)
    write_json_file(USERS_FILE, users)
    write_log(f"Created user: {username}")
    return user


def authenticate_user(username, password):
    users = read_json_file(USERS_FILE)

    for user in users:
        if user["username"] == username and user["password"] == password:
            if not user["is_active"]:
                write_log(f"Inactive user login attempt: {username}")
                return None

            write_log(f"Login successful: {username}")
            return user

    write_log(f"Login failed: {username}")
    return None


def deactivate_user(username):
    users = read_json_file(USERS_FILE)
    found = False

    for user in users:
        if user["username"] == username:
            user["is_active"] = False
            found = True
            write_log(f"Deactivated user: {username}")

    if found:
        write_json_file(USERS_FILE, users)
        return True

    print("User not found")
    return False


def list_users():
    users = read_json_file(USERS_FILE)

    if not users:
        print("No users found")
        return

    for user in users:
        print("-" * 60)
        print(f"User ID: {user['user_id']}")
        print(f"Username: {user['username']}")
        print(f"Full name: {user['full_name']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")
        print(f"Active: {user['is_active']}")


def create_course(title, description, instructor_username, max_students):
    users = read_json_file(USERS_FILE)

    instructor = None
    for user in users:
        if user["username"] == instructor_username and user["role"] == "instructor":
            instructor = user
            break

    if instructor is None:
        print("Instructor not found")
        write_log(f"Course creation failed. Instructor not found: {instructor_username}")
        return None

    courses = read_json_file(COURSES_FILE)

    course = {
        "course_id": generate_id("course"),
        "title": title,
        "description": description,
        "instructor_username": instructor_username,
        "max_students": max_students,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

    courses.append(course)
    write_json_file(COURSES_FILE, courses)
    write_log(f"Created course: {title}")
    return course


def list_courses():
    courses = read_json_file(COURSES_FILE)

    if not courses:
        print("No courses available")
        return

    for course in courses:
        print("-" * 60)
        print(f"Course ID: {course['course_id']}")
        print(f"Title: {course['title']}")
        print(f"Instructor: {course['instructor_username']}")
        print(f"Max students: {course['max_students']}")
        print(f"Active: {course['is_active']}")


def find_course_by_id(course_id):
    courses = read_json_file(COURSES_FILE)

    for course in courses:
        if course["course_id"] == course_id:
            return course

    return None


def find_user_by_username(username):
    users = read_json_file(USERS_FILE)

    for user in users:
        if user["username"] == username:
            return user

    return None


def count_course_enrollments(course_id):
    enrollments = read_json_file(ENROLLMENTS_FILE)
    count = 0

    for enrollment in enrollments:
        if enrollment["course_id"] == course_id and enrollment["status"] == "active":
            count += 1

    return count


def enroll_student(username, course_id):
    user = find_user_by_username(username)

    if user is None:
        print("Student not found")
        write_log(f"Enrollment failed. Student not found: {username}")
        return None

    if user["role"] != "student":
        print("Only students can enroll")
        write_log(f"Enrollment failed. User is not student: {username}")
        return None

    course = find_course_by_id(course_id)

    if course is None:
        print("Course not found")
        write_log(f"Enrollment failed. Course not found: {course_id}")
        return None

    if not course["is_active"]:
        print("Course is not active")
        return None

    current_count = count_course_enrollments(course_id)

    if current_count >= course["max_students"]:
        print("Course is full")
        write_log(f"Enrollment failed. Course full: {course_id}")
        return None

    enrollments = read_json_file(ENROLLMENTS_FILE)

    for enrollment in enrollments:
        if enrollment["username"] == username and enrollment["course_id"] == course_id:
            print("Student already enrolled")
            return None

    enrollment = {
        "enrollment_id": generate_id("enroll"),
        "username": username,
        "course_id": course_id,
        "status": "active",
        "enrolled_at": datetime.now().isoformat()
    }

    enrollments.append(enrollment)
    write_json_file(ENROLLMENTS_FILE, enrollments)
    write_log(f"Student enrolled: {username} in {course_id}")
    return enrollment


def drop_course(username, course_id):
    enrollments = read_json_file(ENROLLMENTS_FILE)
    changed = False

    for enrollment in enrollments:
        if enrollment["username"] == username and enrollment["course_id"] == course_id:
            enrollment["status"] = "dropped"
            enrollment["dropped_at"] = datetime.now().isoformat()
            changed = True
            write_log(f"Student dropped course: {username} from {course_id}")

    if changed:
        write_json_file(ENROLLMENTS_FILE, enrollments)
        return True

    print("Enrollment not found")
    return False


def add_grade(username, course_id, assignment_name, score, max_score):
    user = find_user_by_username(username)

    if user is None:
        print("Student not found")
        return None

    course = find_course_by_id(course_id)

    if course is None:
        print("Course not found")
        return None

    if score < 0 or max_score <= 0:
        print("Invalid score")
        return None

    grades = read_json_file(GRADES_FILE)

    grade = {
        "grade_id": generate_id("grade"),
        "username": username,
        "course_id": course_id,
        "assignment_name": assignment_name,
        "score": score,
        "max_score": max_score,
        "percentage": round((score / max_score) * 100, 2),
        "created_at": datetime.now().isoformat()
    }

    grades.append(grade)
    write_json_file(GRADES_FILE, grades)
    write_log(f"Grade added for {username} in {course_id}")
    return grade


def get_student_grades(username):
    grades = read_json_file(GRADES_FILE)
    student_grades = []

    for grade in grades:
        if grade["username"] == username:
            student_grades.append(grade)

    return student_grades


def calculate_student_average(username):
    grades = get_student_grades(username)

    if not grades:
        return 0

    total_percentage = 0

    for grade in grades:
        total_percentage += grade["percentage"]

    return round(total_percentage / len(grades), 2)


def calculate_course_average(course_id):
    grades = read_json_file(GRADES_FILE)
    course_grades = []

    for grade in grades:
        if grade["course_id"] == course_id:
            course_grades.append(grade["percentage"])

    if not course_grades:
        return 0

    total = 0

    for value in course_grades:
        total += value

    return round(total / len(course_grades), 2)


def generate_student_report(username):
    user = find_user_by_username(username)

    if user is None:
        print("Student not found")
        return None

    enrollments = read_json_file(ENROLLMENTS_FILE)
    courses = read_json_file(COURSES_FILE)
    grades = get_student_grades(username)

    enrolled_courses = []

    for enrollment in enrollments:
        if enrollment["username"] == username and enrollment["status"] == "active":
            for course in courses:
                if course["course_id"] == enrollment["course_id"]:
                    enrolled_courses.append(course)

    report = {
        "student": {
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"]
        },
        "total_active_courses": len(enrolled_courses),
        "average_grade": calculate_student_average(username),
        "courses": enrolled_courses,
        "grades": grades,
        "generated_at": datetime.now().isoformat()
    }

    print(json.dumps(report, indent=2))
    return report


def generate_course_report(course_id):
    course = find_course_by_id(course_id)

    if course is None:
        print("Course not found")
        return None

    enrollments = read_json_file(ENROLLMENTS_FILE)
    users = read_json_file(USERS_FILE)
    grades = read_json_file(GRADES_FILE)

    active_students = []
    course_grades = []

    for enrollment in enrollments:
        if enrollment["course_id"] == course_id and enrollment["status"] == "active":
            for user in users:
                if user["username"] == enrollment["username"]:
                    active_students.append(user)

    for grade in grades:
        if grade["course_id"] == course_id:
            course_grades.append(grade)

    report = {
        "course_id": course["course_id"],
        "title": course["title"],
        "instructor": course["instructor_username"],
        "active_students": len(active_students),
        "average_grade": calculate_course_average(course_id),
        "students": active_students,
        "grades": course_grades,
        "generated_at": datetime.now().isoformat()
    }

    print(json.dumps(report, indent=2))
    return report


def export_users_to_csv(output_file):
    users = read_json_file(USERS_FILE)

    if not users:
        print("No users to export")
        return False

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["user_id", "username", "full_name", "email", "role", "is_active", "created_at"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for user in users:
            writer.writerow({
                "user_id": user["user_id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
                "is_active": user["is_active"],
                "created_at": user["created_at"]
            })

    write_log(f"Exported users to CSV: {output_file}")
    return True


def export_courses_to_csv(output_file):
    courses = read_json_file(COURSES_FILE)

    if not courses:
        print("No courses to export")
        return False

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["course_id", "title", "description", "instructor_username", "max_students", "is_active"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for course in courses:
            writer.writerow({
                "course_id": course["course_id"],
                "title": course["title"],
                "description": course["description"],
                "instructor_username": course["instructor_username"],
                "max_students": course["max_students"],
                "is_active": course["is_active"]
            })

    write_log(f"Exported courses to CSV: {output_file}")
    return True


def backup_all_data():
    ensure_data_directory()

    backup_dir = os.path.join(DATA_DIR, "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")

    backup_data = {
        "users": read_json_file(USERS_FILE),
        "courses": read_json_file(COURSES_FILE),
        "enrollments": read_json_file(ENROLLMENTS_FILE),
        "grades": read_json_file(GRADES_FILE),
        "created_at": datetime.now().isoformat()
    }

    time.sleep(2)

    with open(backup_file, "w", encoding="utf-8") as file:
        json.dump(backup_data, file, indent=2)

    write_log(f"Backup created: {backup_file}")
    return backup_file


def search_students_by_name(keyword):
    users = read_json_file(USERS_FILE)
    results = []

    for user in users:
        if user["role"] == "student":
            if keyword.lower() in user["full_name"].lower():
                results.append(user)

    return results


def search_courses_by_title(keyword):
    courses = read_json_file(COURSES_FILE)
    results = []

    for course in courses:
        if keyword.lower() in course["title"].lower():
            results.append(course)

    return results


def print_dashboard_summary():
    users = read_json_file(USERS_FILE)
    courses = read_json_file(COURSES_FILE)
    enrollments = read_json_file(ENROLLMENTS_FILE)
    grades = read_json_file(GRADES_FILE)

    total_students = 0
    total_instructors = 0
    total_admins = 0

    for user in users:
        if user["role"] == "student":
            total_students += 1
        elif user["role"] == "instructor":
            total_instructors += 1
        elif user["role"] == "admin":
            total_admins += 1

    active_courses = 0
    for course in courses:
        if course["is_active"]:
            active_courses += 1

    active_enrollments = 0
    for enrollment in enrollments:
        if enrollment["status"] == "active":
            active_enrollments += 1

    dashboard = {
        "total_users": len(users),
        "students": total_students,
        "instructors": total_instructors,
        "admins": total_admins,
        "total_courses": len(courses),
        "active_courses": active_courses,
        "active_enrollments": active_enrollments,
        "total_grades": len(grades),
        "generated_at": datetime.now().isoformat()
    }

    print(json.dumps(dashboard, indent=2))
    return dashboard


def seed_sample_data():
    create_user("admin", "admin123", "Admin User", "admin@example.com", "admin")
    create_user("john", "john123", "John Miller", "john@example.com", "student")
    create_user("sarah", "sarah123", "Sarah Wilson", "sarah@example.com", "student")
    create_user("mike", "mike123", "Mike Brown", "mike@example.com", "student")
    create_user("prof_anna", "teacher123", "Anna Schmidt", "anna@example.com", "instructor")
    create_user("prof_mark", "teacher456", "Mark Taylor", "mark@example.com", "instructor")

    python_course = create_course(
        "Python Programming",
        "Learn Python basics, functions, files, and simple automation.",
        "prof_anna",
        30
    )

    devops_course = create_course(
        "DevOps Fundamentals",
        "Learn Git, Jenkins, Docker, Linux, and CI/CD automation.",
        "prof_mark",
        25
    )

    cloud_course = create_course(
        "Cloud Cost Optimization",
        "Understand cloud billing, EC2 pricing, storage cost, and monitoring.",
        "prof_mark",
        20
    )

    if python_course:
        enroll_student("john", python_course["course_id"])
        enroll_student("sarah", python_course["course_id"])
        enroll_student("mike", python_course["course_id"])

        add_grade("john", python_course["course_id"], "Assignment 1", 85, 100)
        add_grade("john", python_course["course_id"], "Assignment 2", 90, 100)
        add_grade("sarah", python_course["course_id"], "Assignment 1", 78, 100)
        add_grade("mike", python_course["course_id"], "Assignment 1", 88, 100)

    if devops_course:
        enroll_student("john", devops_course["course_id"])
        enroll_student("sarah", devops_course["course_id"])

        add_grade("john", devops_course["course_id"], "Docker Lab", 80, 100)
        add_grade("sarah", devops_course["course_id"], "Jenkins Lab", 92, 100)

    if cloud_course:
        enroll_student("mike", cloud_course["course_id"])
        add_grade("mike", cloud_course["course_id"], "EC2 Cost Report", 95, 100)


def risky_admin_action(action_name):
    allowed_actions = ["backup", "dashboard", "export_users", "export_courses"]

    if action_name not in allowed_actions:
        print("Action not allowed")
        write_log(f"Rejected admin action: {action_name}")
        return None

    if action_name == "backup":
        return backup_all_data()

    if action_name == "dashboard":
        return print_dashboard_summary()

    if action_name == "export_users":
        return export_users_to_csv("users_export.csv")

    if action_name == "export_courses":
        return export_courses_to_csv("courses_export.csv")

    return None


def main_menu():
    while True:
        print("\nStudent Course Management System")
        print("1. List users")
        print("2. List courses")
        print("3. Dashboard summary")
        print("4. Student report")
        print("5. Course report")
        print("6. Backup data")
        print("7. Export users")
        print("8. Export courses")
        print("9. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            list_users()

        elif choice == "2":
            list_courses()

        elif choice == "3":
            print_dashboard_summary()

        elif choice == "4":
            username = input("Enter student username: ").strip()
            generate_student_report(username)

        elif choice == "5":
            course_id = input("Enter course ID: ").strip()
            generate_course_report(course_id)

        elif choice == "6":
            backup_file = backup_all_data()
            print(f"Backup created: {backup_file}")

        elif choice == "7":
            export_users_to_csv("users_export.csv")
            print("Users exported")

        elif choice == "8":
            export_courses_to_csv("courses_export.csv")
            print("Courses exported")

        elif choice == "9":
            print("Goodbye")
            break

        else:
            print("Invalid choice")


def main():
    ensure_data_directory()

    users = read_json_file(USERS_FILE)
    courses = read_json_file(COURSES_FILE)

    if not users and not courses:
        print("Seeding sample data...")
        seed_sample_data()

    print_dashboard_summary()

    generate_student_report("john")

    course_list = read_json_file(COURSES_FILE)
    if course_list:
        generate_course_report(course_list[0]["course_id"])

    risky_admin_action("backup")
    risky_admin_action("export_users")
    risky_admin_action("export_courses")


if __name__ == "__main__":
    main()
