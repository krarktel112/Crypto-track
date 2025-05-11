def process_text_file_to_dict(file_path):
    data_dict = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.strip().split(': ')  # Assuming key: value format
                data_dict[key] = value
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except ValueError:
         print(f"Error: Invalid format in line: {line.strip()}")
         return None
    return data_dict
# Example usage
file_path = 'data.txt'  # Replace with your file path

# Create dummy data.txt file
with open(file_path, 'w') as f:
    f.write("name: John Doe\n")
    f.write("age: 30\n")
    f.write("city: New York\n")

data = process_text_file_to_dict(file_path)
if data:
    for key, value in data.items():
        print(f"Key: {key}, Value: {value}")
