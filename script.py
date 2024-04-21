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
    print(f'[PARSING] Parsing TOML file from {path}')
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            print(f'[PARSING] Data: {data}')
    except Exception as e:
        print(f'[PARSING] Error: {e}')
        return None
    # Check if the required fields are present in the TOML file
    if 'submitter' not in data or not all(data['submitter'].get(field) for field in _SUBMITTER_REQUIRED_FIELDS):
        print('[PARSING] Missing submitter information')
        return None
    if 'package' not in data or not all(data['package'].get(field) for field in _PACKAGE_REQUIRED_FIELDS):
        print('[PARSING] Missing package information')
        return None
    return data


def fetch(path: str, updating=False):
    print(f'[FETCH] Fetching data from {path}')
    toml_file = parse_toml(path)
    if toml_file is not None:
        deb_source = toml_file['package']['source']
        # Check if the source is a deb package
        if deb_source is not None and deb_source.startswith('http') and deb_source.endswith('.deb'):
            # Download the deb package and put it in the current directory
            deb_source = parse_url(deb_source, toml_file['package'])
            print(f'[FETCH] Fetching deb package {deb_source}')
            # The deb_source is a URL, so we can use the requests library to download the file
            r = requests.get(deb_source)
            # Extract the file name from the URL and use it as the file name
            file_name = format_package_name(toml_file)
            print(f"[FETCH] Received file: {file_name}")
            arch = toml_file['package']['arch']
            arch = 'amd64' if arch == 'x86_64' else arch
            for file in os.listdir(_APP_DIR):
                if file.endswith('.deb'):
                    if file.startswith(toml_file['package']['name']) and file.endswith(arch + '.deb'):
                        print(f"[FETCH] Removing duplicate:  {file}")
                        os.remove(os.path.join(_APP_DIR, file))

            with open(os.path.join(_APP_DIR, file_name), 'wb') as f:
                print(f"[FETCH] Writing to file: {file_name}")
                f.write(r.content)
            print(f'[FETCH] Deb package saved to {os.path.join(_APP_DIR, file_name)}')
            if updating:
                # Create the signature of the deb package
                signature = subprocess.check_output(['sha256sum', os.path.join(_APP_DIR, file_name)],
                                                    shell=True).decode('utf-8').split()[0]
                print(f'[FETCH] Generated signature: {signature}')
                toml_file['package']['signature'] = signature

            return file_name, toml_file['package']['signature']
        else:
            print('[FETCH] Invalid source')
    else:
        print('[FETCH] Invalid TOML file')
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
    print('[GROUPING] Grouping update files')
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
    print(f'[GROUPING] Zip file created: {zip_file}')


def parse_url(url: str, toml_file_pkg):
    # Replace $pname with the package name and $pversion with the package version
    parsed_url = (url.replace('$pname', toml_file_pkg['name'])
                  .replace('$pversion', toml_file_pkg['version']))
    return parsed_url


def parse_url_compare_release(toml_file_pkg):
    print(f'[COMPARE] Parsing URL {toml_file_pkg["source"]}')
    if 'github.com' in toml_file_pkg['source']:
        # Modify the URL to get the latest release
        final_url = (toml_file_pkg['source']
                     .replace('github.com', 'api.github.com/repos')
                     .replace('releases/download', 'releases/latest'))
        # Remove everything after /latest
        final_url = final_url.split('/latest')[0]
        print(f'[COMPARE] Final URL: {final_url}')
        # Get the latest release version from the GitHub API
        r = requests.get(final_url)
        if r.status_code == 200:
            # Get the latest release version from the JSON object
            latest_version = r.json()['tag_name']
            # Check if the latest release version is different from the package version
            if latest_version != toml_file_pkg['version']:
                print(f'[COMPARE] Latest version: {latest_version}')
                return True, latest_version
            else:
                return False, None


def verify(path: str, output_path='verification.txt', updating=False):
    print(f'[VERIFY] Verifying data from {path}')
    deb_file, signature = fetch(path, updating)
    print(f"[VERIFY] Deb file: {deb_file}, Signature: {signature}")
    deb_file_path = os.path.join(_APP_DIR, deb_file)

    if deb_file is not None and signature is not None:
        output = "=== SIGNATURE VERIFICATION ===\n"
        # Check the SHA256 hash of the deb package
        if updating:
            output += "Skipping signature verification - Generated\n"
        else:
            try:
                print(f"[VERIFY] Checking signature of {deb_file}")
                output += subprocess.check_output(['sha256sum', deb_file_path],
                                                  shell=True, stderr=subprocess.STDOUT).decode('utf-8')
                # If the signature is not equal to the one in the TOML file, return None
                if output.split()[0] != signature:
                    print(f"[VERIFY] Signature mismatch: {output.split()[0]} != {signature}")
                    output += f"\nSignature mismatch: {output.split()[0]} != {signature}\n"
            except subprocess.CalledProcessError as e:
                output += e.output.decode('utf-8').replace('\n', ' ')

        output += "\n=== LINTIAN OUTPUT ===\n"
        # Run lintian on the deb package
        try:
            output += subprocess.check_output(['lintian', deb_file_path],
                                              shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            output += e.output.decode('utf-8').replace('\n', ' ')
        output += "\n=== DPKG-DEB OUTPUT ===\n"
        # dpkg-deb --info
        try:
            output += subprocess.check_output(['dpkg-deb', '--info', deb_file_path],
                                              shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            output += e.output.decode('utf-8').replace('\n', ' ')
        # Write the output to a file
        with open(output_path, 'w') as f:
            f.write(output)
        return output
    else:
        return None


def update():
    print('[UPDATING] Updating data')
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
                    print(f"[UPDATING] Updating {format_package_name(toml_file)} to {latest_version}")
                    # Write new version to the TOML file
                    toml_file['package']['version'] = latest_version
                    to_update_list[file] = toml_file
                else:
                    print(f"[UPDATING] No update available for {format_package_name(toml_file)}")
                    update_error_list[format_package_name(toml_file)] = "No update available"
    # Update the TOML files with the new version
    print('[UPDATING] Updating TOML files versions')
    for file_, data in to_update_list.items():
        with open(os.path.join(_APP_DIR, file_), 'wb') as f_:
            tomli_w.dump(data, f_)
    # Now fetch the new deb packages
    output += "\n=== UPDATED ===\n"
    for file_path, data in to_update_list.items():
        update_path = os.path.join(_UPDATE_DIR, file_path.replace('.toml', '.txt'))
        print(f"[UPDATING] Fetching deb package for {format_package_name(data)}")
        if verify(file_path, update_path):
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
    # The second argument is optional
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
