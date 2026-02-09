source env/bin/activate
sudo aplay -l | grep seeed
sudo apt-get install libportaudio2 portaudio19-dev
git clone https://github.com/jakerella/pi-forecaster
cd pi-forecaster
pip install -r requirements.txt