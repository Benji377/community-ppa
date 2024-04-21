import os
import os.path
import tomllib
import sys
import subprocess
import datetime
import zipfile

import requests
import tomli_w

# Deb package directory
_APP_DIR = 'apps'
# Updates directory
_UPDATE_DIR = 'updates'
# Fields that must be present in the TOML file and not empty
_SUBMITTER_REQUIRED_FIELDS = ['name', 'email', 'is_maintainer']
_PACKAGE_REQUIRED_FIELDS = ['name', 'version', 'summary', 'type', 'license', 'source', 'arch', 'signature']


def parse_toml(path: str):
    print(f'Parsing TOML file from {path}')
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            print(f'Parsed data: {data}')
    except Exception as e:
        print(f'Error: {e}')
        return None
    # Check if the required fields are present in the TOML file
    if 'submitter' not in data or not all(data['submitter'].get(field) for field in _SUBMITTER_REQUIRED_FIELDS):
        print('Missing submitter information')
        return None
    if 'package' not in data or not all(data['package'].get(field) for field in _PACKAGE_REQUIRED_FIELDS):
        print('Missing package information')
        return None

    return data


def fetch(path: str, updating=False):
    print(f'Fetching data from {path}')
    toml_file = parse_toml(path)
    if toml_file is not None:
        deb_source = toml_file['package']['source']
        # Check if the source is a deb package
        if deb_source is not None and deb_source.startswith('http') and deb_source.endswith('.deb'):
            print(f'Fetching deb package {deb_source}')
            # Download the deb package and put it in the current directory
            deb_source = parse_url(deb_source, toml_file['package'])
            # The deb_source is a URL, so we can use the requests library to download the file
            r = requests.get(deb_source)
            # Extract the file name from the URL and use it as the file name
            file_name = format_package_name(toml_file)
            print(f"Received file: {file_name}")
            # If there is already a file starting with the same name, remove it
            # Also remove a file if it has the same name but different version.
            # For example, replace package_1.2.2_amd64.deb with package_1.2.3_amd64.deb
            # It should not remove a file with a different architecture, for example, package_1.2.3_i386.deb
            for file in os.listdir(_APP_DIR):
                if (file.startswith(toml_file['package']['name']) and
                        file.endswith(toml_file['package']['arch'] + '.deb')):
                    os.remove(os.path.join(_APP_DIR, file))

            with open(os.path.join(_APP_DIR, file_name), 'wb') as f:
                f.write(r.content)
            print(f'Deb package saved to {_APP_DIR}')
            if updating:
                # Create the signature of the deb package
                signature = \
                    subprocess.check_output(['sha256sum', os.path.join(_APP_DIR, file_name)]).decode('utf-8').split()[0]
                toml_file['package']['signature'] = signature

            return os.path.join(_APP_DIR, file_name), toml_file['package']['signature']
        else:
            print('Invalid source')
    else:
        return None


def format_package_name(toml_file):
    arch = toml_file['package']['arch']
    arch = 'amd64' if arch == 'x86_64' else arch
    file_name = f"{toml_file['package']['name']}_{toml_file['package']['version']}_{arch}.deb"
    return file_name


def package_update():
    # This function groups all the txt files in the update folder into a single zip file
    # The zip file is named as the current date and time
    # The zip file is then saved to the updates folder and the txt files are removed
    print('Grouping update files')
    # Get the current date and time
    current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # Create a zip file with the current date and time
    zip_file = os.path.join(_UPDATE_DIR, f'{current_date}.zip')
    # Iterate through all the files in the updates directory
    with zipfile.ZipFile(zip_file, 'w') as z:
        for file in os.listdir(_UPDATE_DIR):
            if file.endswith('.txt'):
                # Add the file to the zip file
                z.write(os.path.join(_UPDATE_DIR, file), file)
                # Remove the file
                os.remove(os.path.join(_UPDATE_DIR, file))
    print(f'Zip file created: {zip_file}')


def parse_url(url: str, toml_file_pkg):
    # Replace $pname with the package name and $pversion with the package version
    parsed_url = (url.replace('$pname', toml_file_pkg['name'])
                  .replace('$pversion', toml_file_pkg['version']))
    return parsed_url


def parse_url_compare_release(toml_file_pkg):
    print(f'Parsing URL {toml_file_pkg["source"]}')
    # This function first checks if the given URL is a valid GitHub URL
    # If it is, it will try to check the latest release version of the repository
    # If the version is not the same as the latest release, it will return True and the URL of the latest release
    # If the version is the same as the latest release, it will return False
    # If the URL is not a valid GitHub URL, it will return None
    if 'github.com' in toml_file_pkg['source']:
        # Modify the URL to get the latest release
        final_url = toml_file_pkg['source'].replace('github.com', 'api.github.com/repos').replace('releases/download',
                                                                                                  'releases/latest')
        # Remove everything after /latest
        final_url = final_url.split('/latest')[0]
        print(f'Final URL: {final_url}')
        # Get the latest release version from the GitHub API
        r = requests.get(final_url)
        if r.status_code == 200:
            # Get the latest release version from the JSON object
            latest_version = r.json()['tag_name']
            # Check if the latest release version is different from the package version
            if latest_version != toml_file_pkg['version']:
                print(f'Latest version: {latest_version}')
                return True, latest_version
            else:
                return False, None


def verify(path: str, output_path='verification.txt'):
    print(f'Verifying data from {path}')
    deb_file, signature = fetch(path)
    if deb_file is not None and signature is not None:
        output = "=== SIGNATURE VERIFICATION ===\n"
        # Check the SHA256 hash of the deb package
        try:
            output += subprocess.check_output(['sha256sum', deb_file]).decode('utf-8')
            # If the signature is not equal to the one in the TOML file, return None
            if output.split()[0] != signature:
                print(f"Signature mismatch: {output.split()[0]} != {signature}")
        except subprocess.CalledProcessError as e:
            output += e.output.decode('utf-8')

        output += "\n=== LINTIAN OUTPUT ===\n"
        # Run lintian on the deb package
        try:
            output += subprocess.check_output(['lintian', deb_file], stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            output += e.output.decode('utf-8')
        output += "\n=== DPKG-DEB OUTPUT ===\n"
        # dpkg-deb --info
        try:
            output += subprocess.check_output(['dpkg-deb', '--info', deb_file], stderr=subprocess.STDOUT).decode(
                'utf-8')
        except subprocess.CalledProcessError as e:
            output += e.output.decode('utf-8')
        print(output)
        # Write the output to a file
        with open(output_path, 'w') as f:
            f.write(output)
        return output
    else:
        return None


def update():
    print('Updating data')
    # Iterate through all the files in the apps directory, parse the TOML file and fetch the deb package
    output = "=== NEED UPDATE ===\n"
    to_update_list = {}
    update_error_list = {}
    for file in os.listdir(_APP_DIR):
        if file.endswith('.toml'):
            toml_file = parse_toml(os.path.join(_APP_DIR, file))
            if toml_file is not None and toml_file['package']['auto_update']:
                to_update, latest_version = parse_url_compare_release(toml_file['package'])
                if to_update:
                    output += f"- {format_package_name(toml_file)}: {toml_file['package']['source']} -> {latest_version}\n"
                    # Write new version to the TOML file
                    toml_file['package']['version'] = latest_version
                    to_update_list[file] = toml_file
                else:
                    update_error_list[format_package_name(toml_file)] = "No update available"
    # Update the TOML files with the new version
    for file, data in to_update_list.items():
        with open(os.path.join(_APP_DIR, file), 'wb') as f:
            tomli_w.dump(data, f)
    # Now fetch the new deb packages
    output += "\n=== UPDATED ===\n"
    for file, data in to_update_list.items():
        file_path, signature = fetch(os.path.join(_APP_DIR, file), True)
        if file_path is not None and signature is not None:
            # Add signature to the TOML file
            data['package']['signature'] = signature
            with open(os.path.join(_APP_DIR, file), 'wb') as f:
                tomli_w.dump(data, f)
            # Verify the deb package
            update_path = os.path.join(_UPDATE_DIR, file.replace('.toml', '.txt'))
            verify(file_path, update_path)
            output += f"- {format_package_name(data)} updated\n"
        else:
            update_error_list[format_package_name(data)] = "Error fetching deb package"
    output += "\n=== NOT UPDATED ===\n"
    for file, error in update_error_list.items():
        output += f"- {file}: {error}\n"

    # Write the output to a file
    update_log = os.path.join(_UPDATE_DIR, 'update_log.txt')
    with open(update_log, 'w') as f:
        f.write(output)


# Main function with arguments, which will be passed to the script
#  has two arguments: action and path
def main(action: str, path: str):
    # Check if the action is 'create'
    if action == 'verify':
        if path is None or path == '':
            print('Missing argument: path')
        else:
            verify(path)
    elif action == 'update':
        update()
        package_update()
    elif action == 'delete':
        print('Not yet implemented')
    else:
        print(f'Invalid action: {action}')


if __name__ == '__main__':
    # Pass the arguments to the main function
    main(sys.argv[1], sys.argv[2])
