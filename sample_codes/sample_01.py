password = "admin123"

def login(username, password_input):
    if username == "admin" and password_input == password:
        return True
    return False

print(login("admin", "admin123"))
