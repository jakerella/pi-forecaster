source env/bin/activate
ls /dev/i2c* /dev/spi*
python3 test/blinka.py
sudo i2cdetect -y 1
sudo apt-get install -y git
git clone https://github.com/HinTak/seeed-voicecard
cd seeed-voicecard
git checkout v6.12
sudo ./install.sh
sudo reboot