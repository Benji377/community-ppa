# Community PPA
# About
An extension to the main apt repository containing community-made applications and games. \
Still a work in progress

## Use this PPA
Simply execute the following commands:
```
curl -s --compressed "https://Benji377.github.io/community-ppa/KEY.gpg" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/community-ppa.gpg >/dev/null
sudo curl -s --compressed -o /etc/apt/sources.list.d/app_list.list "https://Benji377.github.io/community-ppa/app_list.list"
sudo apt update
```
And then you can install all the packages of this repository using:
```
sudo apt install package_name
```
You can find a list of all the packages in this repository below.

## How to add or update your package
- Your .deb package must be a valid package. You should test-install it on your system first
- Then, simply create a PR request where you add your .deb package to the apps directory
- Or when updating, replace your old package with the new one
- Remember to also update the README by adding your package name to it in alphabetical order and a short description
- Once verified, your package will be added to the list

## Package list
- [raspirus](https://github.com/Raspirus/Raspirus) A signature based malware scanner
