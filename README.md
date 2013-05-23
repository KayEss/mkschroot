# mkschroot #


A simple script for making schroot environments from a JSON configuration file

This first version isn't so smart. It assumes that you're using a 64 bit host machine, and doesn't check that you're on Debian as it should (it only uses `debootstrap` to build the chroot environment).


## Using mkschroot ##

You need to pass mkschroot a configuration file:

    mkschroot ~/chroots/example.json

The configuration file needs to be JSON. A chroot is described by a structure like the following:

    {
        "release": "lucid",
        "conf": {
            "root-users": ["kirit'"],
            "users": ["kirit"]
        }
    }

* `release`: The operating system version you wish to make use of.
* `conf`: The fields used for the schroot configuration file (in `/etc/schroot/chroot.d/`). The following fields are required: `root-users`, `users`, and the following are optional: `description`. Do read the part about common fields though.

