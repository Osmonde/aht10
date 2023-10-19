# aht10
Logging utilities for the AHT10 temperature sensor.

This script is designed to be a simple logging utility for the AHT10 i2c temperature/humidity sensor.

## Invocation
This script is meant to run in the background as a daemon, the stock configuration is set to log values every 60 seconds. A systemd unit file is included to run the script out of /var/log/sbin.

## TODO
Some extra features that would be nice to have
* CLI flags for runtime variables
* Configurable interval
* Support logging to HTTP endpoints such as elastic search. 
* Ensure systemd properly watches and restarts process. 

## Known Issues
Date rotation of the log file via python's logging library does not seem to work as expected, this is a work in progress. 
