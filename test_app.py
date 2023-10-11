import requests


# Define the base URL of your FastAPI application
base_url = 'http://localhost:8001'
assignment_id= '564754cnvb mn'
# Helper function to print the response in a readable format
def print_response(response):
    print(f'Status Code: {response.status_code}')
    print('Response Body:')
    print(response.text)
    print()

# Test the Health Check Endpoint
health_check_url = f'{base_url}/healthz'
response = requests.get(health_check_url)
print('Health Check:')
print_response(response)

# Test the Get All Assignments Endpoint
all_assignments_url = f'{base_url}/v1/all_assignments'
response = requests.get(all_assignments_url)
print('Get All Assignments:')
print_response(response)


user_assignments_url = f'{base_url}/v1/assignments'
response = requests.get(user_assignments_url)
print('Get User Assignments:')
print_response(response)

# Test the Create Assignment Endpoint
create_assignment_url = f'{base_url}/v1/create_assignment'
assignment_data = {
    "title": "New Assignment",
    "description": "Description of New Assignment",
    "points": 5,
    "num_of_attempts": 2
}
response = requests.post(create_assignment_url, json=assignment_data)
print('Create Assignment:')
print_response(response)

# Test the Update Assignment Endpoint (replace {assignment_id} with an actual assignment ID)
update_assignment_url = f'{base_url}/v1/assignment/{assignment_id}'
update_data = {
    "title": "Updated Assignment",
    "description": "Updated Description",
    "points": 8,
    "num_of_attempts": 3
}
response = requests.put(update_assignment_url, json=update_data)
print('Update Assignment:')
print_response(response)

# Test the Delete Assignment Endpoint (replace {assignment_id} with an actual assignment ID)
delete_assignment_url = f'{base_url}/v1/assignment/{assignment_id}'
response = requests.delete(delete_assignment_url)
print('Delete Assignment:')
print_response(response)

# Authentication: To test authentication-protected endpoints, you can use requests with HTTP Basic Auth.
# Replace "username" and "password" with valid credentials for testing.
auth = ("vyshu@gmail.com", "hello")
protected_url = f'{base_url}/v1/protected_endpoint'
response = requests.get(protected_url, auth=auth)
print('Authentication:')
print_response(response)
