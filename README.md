# community-ppa
# About
WORK IN PROGRESS

## Use this PPA
Simply execute the following commands:
```
curl -s --compressed "https://Benji377.github.io/community-ppa/KEY.gpg" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/community-ppa.gpg >/dev/null
sudo curl -s --compressed -o /etc/apt/sources.list.d/my_list_file.list "https://Benji377.github.io/community-ppa/app_list.list"
sudo apt update
```
And then you can install all the packages using:
```
sudo apt install package_name
```

## How to add your package
### Prerequisites
- Have a .deb package

### 0. Setup
- Install `gpg`, `dpkg-dev`, `apt-utils`, `git` and `gzip`
  ```sh
  sudo apt install gpg dpkg-dev apt-utils git gzip
  ```
- Clone this repository and copy the `.deb` package to it
  ```
  git clone "https://github.com/Benji377/community-ppa.git"
  cd apps
  cp /path/to/my/package_0.0.1_amd64.deb .
  ```
  
### 1. Creating a GPG key
Start with:
```
gpg --full-gen-key
```
Use RSA:
```
Please select what kind of key you want:
   (1) RSA and RSA (default)
   (2) DSA and Elgamal
   (3) DSA (sign only)
   (4) RSA (sign only)
Your selection? 1
```
RSA with 4096 bits:
```
RSA keys may be between 1024 and 4096 bits long.
What keysize do you want? (3072) 4096
```
Key should be valid forever:
```
Please specify how long the key should be valid.
0 = key does not expire
<n> = key expires in n days
<n>w = key expires in n weeks
<n>m = key expires in n months
<n>y = key expires in n years
Key is valid for? (0) 0
Key does not expire at all
Is this correct? (y/N) y
```
Enter your name and email:
```
Real name: My Name
Email address: ${EMAIL}
Comment:
You selected this USER-ID:
"My Name <my.name@email.com>"

Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O
```
At this point the `gpg` command will start to create your key and will ask for a passphrase for extra protection.
You can back up your private key with:
```
gpg --export-secret-keys "${EMAIL}" > my-private-key.asc
```
and import it using:
```
gpg --import my-private-key.asc
```

### 2. Creating the `KEY.gpg` file
Create the ASCII public key file KEY.gpg inside the git repo:
```
gpg --armor --export "${EMAIL}" > /path/to/community-ppa/KEY.gpg
```
Note: The private key is referenced by the email address you entered in the previous step.

### 3. Creating the `Packages` and `Packages.gz` files
Inside the git repo:
```
dpkg-scanpackages --multiversion . > Packages
gzip -k -f Packages
```

### 4. Creating the `Release`, `Release.gpg` and `InRelease` files
Inside the git repo my_ppa:
```
apt-ftparchive release . > Release
gpg --default-key "${EMAIL}" -abs -o - Release > Release.gpg
gpg --default-key "${EMAIL}" --clearsign -o - Release > InRelease
```

## How to update your packages
Just put your new `.deb` file into the git repository and execute:
```
# Packages & Packages.gz
dpkg-scanpackages --multiversion . > Packages
gzip -k -f Packages

# Release, Release.gpg & InRelease
apt-ftparchive release . > Release
gpg --default-key "${EMAIL}" -abs -o - Release > Release.gpg
gpg --default-key "${EMAIL}" --clearsign -o - Release > InRelease

# Commit & push
git add -A
git commit -m update
git push
```
