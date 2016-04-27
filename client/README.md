Surviveler client
=================

# Setup
To bootstrap the development environment and install dependencies, from client's
top directory (the one which contains this README file) execute the setup
script:

```
scripts/setup.sh
```

# Running
To start the client, run the following script from client's top directory:

```
scripts/run.sh
```

# Manual setup for fish shell

## Create the appropriate virualenv using virtualfish
To use the fish shell at your best you should install globally virtualfish with

    pip install virtualfish

Then go inside the `surviveler/client` directory and create a virtualfish env:

    # Create the environment and activate it (python3 is the python executable you
    # want to use)
    vf new -p python3 surviveler
    vf activate surviveler

    # When in surviveler/client with the environment activated you can optionally
    # connect it so that it's being activated autmatically every time you enter in
    # the directory
    vf connect

Congratulations, you have a working environment using virtualfish.

## Manual installing dependencies with pip
To install all the required dependencies you will have to be inside the
`surviveler/client` directory and have the environment activated.

Then this command will do the trick.

    pip install -r requirements.txt

## Running the application in the fish shell
From within the virtualenv:

    python src/main.py

# Configuration
It is possible to tweak various parameters of the client using the client.ini
config file. Some useful parameters that can be changed are:

 * **[Network] ServerIPAddress** if you need to connect on a server hosted elsewher than
 localhost

 * **[Logging] Level** is the level of logging for the client:

  * *NOTSET*: I have no idea about what this level means, actually.
  * *DEBUG*: huge amount of noise, useful for debug, useless for production.
  * *INFO*: main pieces of information about the game. No spam.
  * *WARNING*: not used yet.
  * *ERROR*: not used yet.
  * *CRITICAL*: not used yet.
