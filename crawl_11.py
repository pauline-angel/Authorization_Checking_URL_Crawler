from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, urljoin
import re
from tabulate import tabulate

def extract_paths_from_source(source, base_url):
    """Extracts all paths from href, src, and action attributes in the page source."""
    paths = set()
    attributes = ['href', 'src', 'action']

    for attr in attributes:
        # Find all occurrences of the attribute in the source code
        matches = re.findall(f'{attr}=["\'](.*?)["\']', source, re.IGNORECASE)
        for match in matches:
            # Join relative paths with the base URL to form a full URL
            full_url = urljoin(base_url, match)
            paths.add(full_url)

    return paths

def filter_subdomain_paths(paths, main_domain):
    """Filters paths to include only those that are subdomains of the main domain."""
    filtered_paths = set()
    for path in paths:
        parsed_url = urlparse(path)
        if parsed_url.netloc.endswith(main_domain):
            filtered_paths.add(path)
    return filtered_paths

def print_paths_in_table(paths):
    """Prints the paths in a tabular format."""
    sorted_paths = sorted(paths)
    print(tabulate([(path,) for path in sorted_paths], headers=["Path"], tablefmt="grid"))

def find_ids_in_urls(paths):
    """Finds URLs with IDs (integers, 'True', or 'False') after an '=' symbol."""
    id_paths = set()

    # Regex to match IDs that are integers, True, or False after any parameter
    id_regex = re.compile(r'=[0-9]+|=True|=False|=true|=false', re.IGNORECASE)

    for path in paths:
        if id_regex.search(path):
            id_paths.add(path)

    return id_paths

def compare_and_print_common_paths(user_paths, admin_paths):
    """Compares the links of user and admin pages and prints the paths side by side, with common paths separately."""
    common_paths = user_paths.intersection(admin_paths)

    # Convert paths to sorted lists
    user_paths_list = sorted(user_paths)
    admin_paths_list = sorted(admin_paths)

    # Prepare data for side-by-side table
    max_length = max(len(user_paths_list), len(admin_paths_list))
    user_paths_list.extend([""] * (max_length - len(user_paths_list)))  # Pad the shorter list with empty strings
    admin_paths_list.extend([""] * (max_length - len(admin_paths_list)))

    side_by_side_table = list(zip(user_paths_list, admin_paths_list))

    # Print the side-by-side table
    print("\nLinks Available in User1 and User2 Pages:")
    print(tabulate(side_by_side_table, headers=["User1 Paths", "User2 Paths"], tablefmt="grid"))

    # Find and print URLs with IDs
    user_id_paths = find_ids_in_urls(user_paths)
    admin_id_paths = find_ids_in_urls(admin_paths)

    # Convert to sorted lists for table display
    user_id_paths_list = sorted(user_id_paths)
    admin_id_paths_list = sorted(admin_id_paths)

    # Prepare the data for tabular display
    max_length_ids = max(len(user_id_paths_list), len(admin_id_paths_list))
    user_id_paths_list.extend([""] * (max_length_ids - len(user_id_paths_list)))  # Pad the shorter list
    admin_id_paths_list.extend([""] * (max_length_ids - len(admin_id_paths_list)))

    table = list(zip(user_id_paths_list, admin_id_paths_list))

    print("\n(Possible IDOR) Links with IDs in User1 and User2 Pages:")
    print(tabulate(table, headers=["User1", "User2"], tablefmt="grid"))

def access_uncommon_paths(driver, uncommon_paths, user_credentials, main_domain, paths_owner_name):
    """Attempts to access the paths of the given user using another user's credentials."""
    print(f"\nAttempting to access {paths_owner_name}'s paths using {user_credentials['username']}'s credentials:")

    # Log in as the current user
    driver.get(input(f"Give the login page URL for {user_credentials['username']}:"))
    username = driver.find_element(By.NAME, value=user_credentials['username_field'])
    password = driver.find_element(By.NAME, value=user_credentials['password_field'])
    username.send_keys(user_credentials['username'])
    password.send_keys(user_credentials['password'])
    login_button = driver.find_element(By.XPATH, '//*[@id="login"]')
    login_button.click()

    for path in uncommon_paths:
        try:
            # Attempt to access the path while logged in as the current user
            driver.get(path)
            page_content = driver.page_source.lower()
            current_url = driver.current_url.lower()

            # Check if page content indicates access denied
            if any(error in page_content for error in ["403 forbidden", "404 not found", "login", "signin", "log in"]):
                print(f"Authorization Bypass Failed")
                print(f"Access denied to {path} (Content shows error or login page)")
            elif urlparse(current_url).netloc.endswith(main_domain) and current_url != path.lower():
                print(f"Authorization Bypass Failed")
                print(f"Access denied to {path} (redirected back to main domain)")
            else:
                print(f"Authorization Bypass Successful")
                print(f"Successfully accessed {path} as {user_credentials['username']}")

        except Exception as e:
            print(f"Failed to access {path}: {e}")

# Main script
if __name__ == "__main__":
    # Set up the WebDriver using webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Step 1: Log in as the first user and extract paths
    driver.get(input("Give the login page URL for user1:"))

    # Fill in the login credentials
    user1_credentials = {
        'username_field': input("Give the Username field parameter for User1:"),
        'password_field': input("Give the Password field parameter for User1:"),
        'username': input("Give the user1 Username:"),
        'password': input("Give the user1 Password:")
    }
    username = driver.find_element(By.NAME, value=user1_credentials['username_field'])
    password = driver.find_element(By.NAME, value=user1_credentials['password_field'])
    username.send_keys(user1_credentials['username'])
    password.send_keys(user1_credentials['password'])

    # Wait for the login button to be clickable and click it
    login_button = driver.find_element(By.XPATH, '//*[@id="login"]')
    login_button.click()

    # User-provided URL after login
    user_provided_url = input("Give the URL after login for user1:")

    # Get the page source of the user's post-login page
    driver.get(user_provided_url)
    user_page_source = driver.page_source

    # Extract paths from the user's post-login page
    user_main_domain = urlparse(user_provided_url).netloc
    user_paths = extract_paths_from_source(user_page_source, user_provided_url)
    user_filtered_paths = filter_subdomain_paths(user_paths, user_main_domain)

    # Step 2: Log in as the second user and extract paths
    driver.get(input("Give the login page URL for user2:"))

    # Fill in the login credentials for the second user
    user2_credentials = {
        'username_field': input("Give the Username field parameter for User2:"),
        'password_field': input("Give the Password field parameter for User2:"),
        'username': input("Give the user2 Username:"),
        'password': input("Give the user2 Password:")
    }
    username = driver.find_element(By.NAME, value=user2_credentials['username_field'])
    password = driver.find_element(By.NAME, value=user2_credentials['password_field'])
    username.send_keys(user2_credentials['username'])
    password.send_keys(user2_credentials['password'])

    # Wait for the login button to be clickable and click it
    login_button = driver.find_element(By.XPATH, '//*[@id="login"]')
    login_button.click()

    # User-provided URL after login
    admin_provided_url = input("Give the URL after login for user2:")

    # Get the page source of the second user's post-login page
    driver.get(admin_provided_url)
    admin_page_source = driver.page_source

    # Extract paths from the second user's post-login page
    admin_main_domain = urlparse(admin_provided_url).netloc
    admin_paths = extract_paths_from_source(admin_page_source, admin_provided_url)
    admin_filtered_paths = filter_subdomain_paths(admin_paths, admin_main_domain)

    # Step 3: Compare paths and print the common paths, including those with IDs
    compare_and_print_common_paths(user_filtered_paths, admin_filtered_paths)

    # Step 4: Access uncommon paths using each other's credentials
    user_uncommon_paths = user_filtered_paths - admin_filtered_paths
    admin_uncommon_paths = admin_filtered_paths - user_filtered_paths

    # Access User1's uncommon paths with User2's credentials
    access_uncommon_paths(driver, user_uncommon_paths, user2_credentials, user_main_domain, "User1")

    # Access User2's uncommon paths with User1's credentials
    access_uncommon_paths(driver, admin_uncommon_paths, user1_credentials, admin_main_domain, "User2")

    driver.quit()
