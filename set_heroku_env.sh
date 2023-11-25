#!/bin/bash

# Set the app name
HEROKU_APP_NAME="memory-center-backend"

# Loop through each line in .env file
while IFS='=' read -r key value; do
  # Skip empty lines and lines starting with #
  if [ -z "$key" ] || [[ "$key" == \#* ]]; then
    continue
  fi

  # Set the config var in Heroku
  heroku config:set "$key=$value" -a $HEROKU_APP_NAME
done < .env
