from dotenv import load_dotenv

import argparse
import subprocess
import os

load_dotenv()
rpc_username = os.environ.get("RPC_USER")
rpc_password = os.environ.get("RPC_PASS")


def timestamp_signature(signature_data, output_path):
    # Save the signature to a specified output file path
    with open(output_path, 'w') as file:
        file.write(signature_data)

    # Base filename without extension
    temp_filename = os.path.splitext(output_path)[0]

    # Use opentimestamps to timestamp the file
    try:
        # Run the ots stamp command on the file
        subprocess.run(['ots', 'stamp', output_path], check=True)
        
        # The .ots file is created with the same name as the temp file but with .ots extension
        ots_filename = temp_filename + '.ots'
        
        # Check if the .ots file was created successfully
        if os.path.exists(ots_filename):
            print("Timestamp successfully created:", ots_filename)
            return ots_filename
        else:
            print("Failed to create timestamp.")
            return None
    finally:
        # Optionally remove the signature file if no longer needed
        os.remove(output_path)

def verify_timestamp(ots_file_path):
    # Ensure the .ots file exists
    if not os.path.isfile(ots_file_path):
        print("Timestamp file does not exist.")
        return

    # Use opentimestamps to verify the timestamp
    try:
        # Execute the ots verify command and capture the output
        result = subprocess.run(['ots', '--bitcoin-node', f'http://{rpc_username}:{rpc_password}@127.0.0.1:8332/', 'verify', ots_file_path], capture_output=True, text=True)
        print(result)
        # Print the output of the command
        if result.returncode == 0:
            print("Verification successful:")
            print(result.stderr)
            return True
        else:
            print("Verification failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print("An error occurred during verification:", str(e))
        return False

def main():
    # parser = argparse.ArgumentParser(description='Timestamp a signature using OpenTimestamps.')
    # parser.add_argument('signature_data', type=str, help='Signature content to be timestamped.')
    # parser.add_argument('output_path', type=str, help='Output path for the timestamped file.')
    # args = parser.parse_args()

    # # Call the function with arguments from the command line
    # ots_file = timestamp_signature(args.signature_data, args.output_path)
    # if ots_file:
    #     print("Created timestamp file:", ots_file)

    # ots_file_path = 'opentimestamps-client/examples/hello-world.txt.ots'  # Replace with your actual .ots file path
    # verification_result = verify_timestamp(ots_file_path)
    pass

if __name__ == "__main__":
    main()