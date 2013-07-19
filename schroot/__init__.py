import os

from chroot import Schroot


def execute(program, *args):
    """
        Execute a program and return True if it worked.
    """
    command = '%s %s' % (program, ' '.join([str(a) for a in args]))
    print "Starting", command
    assert os.system(command) == 0


def sudo(program, *args):
    """
        Execute a program with sudo rights
    """
    return execute("sudo", program, *args)

