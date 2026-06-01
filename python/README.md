# U-Interoperability: Python Version

In order to use the scripts in this folder, first create a virtual environment.

## Installing the virtual environment

To install the python virtual environment tool, use the following command.

```bash
# On Windows
> pip install virtualenv

# On Linux
$ sudo apt install python3-venv
```

## Creating a virtual environment

Create a virtual environment in the root directory of the repository using the following commands.

```bash
$ cd path/to/root
$ python3 -m venv ./.venv
```

Afterward, activate the virtual environment and install the required dependencies.

```bash
$ source .venv/bin/activate
(.venv) $ pip install -r ./python/requirements.txt
```