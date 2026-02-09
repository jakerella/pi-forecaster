# Pi Forecaster

A repo to use a RasPi Zero W as a weather forecaster.

https://learn.adafruit.com/adafruit-voice-bonnet/raspberry-pi-setup

1. Buy stuff
2. Install Raspian Lite
3. Run setup-1.sh, reboot, continue with the rest
4. Create `.env` from `.env.example` and add GEN_AI_KEY for Google GenAI
5. Run test scripts as needed
6. Run from CLI to test
    - `cd pi-forecaster/` (if not already there)
    - `source ../env/bin/activate` (if not already active)
    - `python forecaster/forecaster.py` (wait for green lights)
    - press button
7. Install as a service
    - `cp pi-forecaster.service /etc/systemd/system/pi-forecaster.service`
    - `sudo systemctl daemon-reload`
    - `sudo systemctl enable pi-forecaster.service`
    - `sudo systemctl restart pi-forecaster.service` (to start/restart the service)
    - `sudo systemctl status pi-forecaster.service` (just to see it is running)
    - `journalctl -u pi-forecaster.service -f` (to see/follow logs)
    - `sudo systemctl stop pi-forecaster.service` (to stop the service)


TODO:
- clear up wav file cache
- trigger by voice
- allow for different day inputs
- allow for different location inputs (with geocoding)
- better readme
- test out all setup scripts
- have input for setup scripts (like username, genAI API key etc)
