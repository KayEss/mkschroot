import os
import tempfile


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


def create_root_file(location, content):
    """
        Create the file at location with the requested content.
        The file will be owned by root, but be world readable.
    """
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(content)
    tmp_file.close()
    sudo("mv", tmp_file.name, location)
    sudo("chown", "root:root", location)
    sudo("chmod", "a+r", location)


def current_user():
    """
        Return the name of the currently logged in user.
    """
    return os.environ["USER"]

