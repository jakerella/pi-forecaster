# Pi Forecaster

A repo to use a RasPi as a weather forecaster.


To update autostartup config:
`nano /etc/systemd/system/pi-forecaster.service`

Set to start at boot:

`sudo systemctl enable pi-forecaster.service`

or disable at boot:

`sudo systemctl disable pi-forecaster.service`

check status:

`sudo systemctl status pi-forecaster.service`
