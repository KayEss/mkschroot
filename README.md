# mkschroot #


A simple script for making schroot environments from a JSON configuration file

This first version isn't so smart. It assumes that you're using a 64 bit host machine, and doesn't check that you're on Debian as it should (it only uses `debootstrap` to build the chroot environment). It's probably also highly Ubuntu specific right now.


## Using mkschroot ##

You need to pass mkschroot a configuration file:

    mkschroot ~/chroots/example.json

### Configuring mkschroot ###

The configuration file needs to be JSON. A full sample configuration might look like the below:

    {
        "root": "/mnt/files2/chroot",
        "source": "http://th.archive.ubuntu.com/ubuntu/",
        "base-packages": ["openssh-client"],
        "defaults": {
            "conf": {
                "root-users": ["kirit"],
                "users": ["kirit"]
            }
        },
        "schroot": {
            "build-lucid64": {
                "release": "lucid",
                "packages": [
                    "g++", "libbz2-dev", "libssl-dev", "python-dev", "uuid-dev",
                    "boost-build", "libboost-all-dev"
                ]
            },
            "root-ca-kirit": {
                "release": "precise",
                "packages": ["openssl"],
                "conf": {
                    "personality": "linux32"
                }
            }
        }
    }

A chroot is described by a structure like the following:

    {
        "release": "lucid",
        "conf": {
            "root-users": ["kirit'"],
            "users": ["kirit"]
        }
    }

* `release`: The operating system version you wish to make use of.
* `conf`: The fields used for the schroot configuration file (in `/etc/schroot/chroot.d/`). The following fields are required: `root-users`, `users`, and the following are optional: `description`. Do read the part about common fields though.

#### Common configuration items ####

Generally many of the chroots that you want will share a good deal of configuration between machines. To help with this a default `schroot` configuration can be given which will then have values overridden by the specific `schroot`s that you request be made.

