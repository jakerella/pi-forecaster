sudo apt update
sudo apt-get -y upgrade
sudo apt install --upgrade python3-setuptools
sudo apt-get install -y python3-pip
sudo apt install python3-venv
python -m venv env --system-site-packages
sudo reboot