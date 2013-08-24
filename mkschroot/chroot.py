import os
import subprocess

from mkschroot import create_root_file, current_user,  execute, sudo


PERSONALITY = 'linux64' # Assume 64 bit for now
ARCH = { # Allow us to find the architecture from the personality name
    'linux64': 'amd64',
    'linux32': 'i386',
}


def _caller(caller):
    """
        Decorator to allow us to print the command we're running
    """
    def call(command, **opts):
        print ' '.join(command)
        if opts:
            print opts
        return caller(command, **opts)
    return call


class Schroot(dict):
    def __init__(self, config, name, source, base_packages, http_proxy):
        """
            Build a chroot configuration by mixing the global and local configuration.
        """
        super(Schroot, self).__init__(conf={}, sources={})
        self.name = name
        self.source = source
        self.http_proxy = http_proxy
        def copy_into(struct):
            for key, value in struct.items():
                if key in ["conf", "sources"]:
                    for conf, choice in value.items():
                        self[key][conf] = choice
                else:
                    self[key] = value
        copy_into(config['defaults'])
        copy_into(config['schroot'][name])
        def ensure(conf, value):
            if not self['conf'].has_key(conf):
                self['conf'][conf] = value
        ensure('directory', os.path.join(config['root'], name))
        ensure('personality', PERSONALITY)
        ensure('type', 'directory')
        ensure('description', '%s %s' % (
            self['release'], self['conf']['personality']))
        ensure('root-users', [current_user()])
        ensure('users', [current_user()])
        self['packages'] = self.get('packages', []) + base_packages
        for source, source_conf in self['sources'].items():
            if not source_conf.has_key('source'):
                source_conf['source'] = config['source']
        if self.has_key("variant"):
            for setup in ['config', 'copyfiles', 'fstab', 'nssdatabases']:
                if os.path.exists('/etc/schroot/%s/%s' % (self['variant'], setup)):
                    ensure("setup.%s" % setup, "%s/%s" % (self['variant'], setup))


    def chroot_path(self, path):
        """
            Return a path within the chroot given a root relative path.
        """
        return os.path.join(self['conf']['directory'], path)


    def check_call(self, program, directory='/', caller=subprocess.check_call):
        """
            Execute the program within the schroot.
        """
        return (_caller(caller))(
            ['schroot', '--chroot', self.name, '--directory', directory, '--'] + program)


    def sudo(self, program, directory='/home/', caller=subprocess.check_call):
        """
            Execute the program as root in the schroot environment.
        """
        return (_caller(caller))(
            ['schroot', '--chroot', self.name, '--user', 'root',
                '--directory', directory, '--'] + program)


    def update_conf_file(self):
        """
            Ensure that the schroot configuration file is correct.
        """
        conf_file = '[%s]\n' % self.name
        for conf, value in self['conf'].items():
            if conf == 'personality' and value == PERSONALITY:
                value = None
            elif issubclass(type(value), list):
                value = ','.join(value)
            if value:
                conf_file += "%s=%s\n" % (conf, value)
        file_loc = os.path.join('/etc/schroot/chroot.d/', self.name)
        if not os.path.exists(file_loc) or file(file_loc, "r").read() != conf_file:
            create_root_file(file_loc, conf_file)


    def update_packages(self):
        """
            Ensure that the schroot is properly built and has the latest packages.
        """

        # If /etc/ isn't in the VM then we don't have a proper install yet
        if not os.path.exists(os.path.join(self['conf']['directory'], 'etc/')):
            bootstrap = ["debootstrap"]
            if self.has_key('variant'):
                bootstrap.append("--variant=%s" % self["variant"])
            bootstrap.append("--arch=%s" % ARCH[self['conf']['personality']])
            bootstrap.append(self['release'])
            bootstrap.append(self['conf']['directory'])
            bootstrap.append(self.source)
            if self.http_proxy:
                bootstrap.insert(0, 'http_proxy="%s"' % self.http_proxy)
            sudo(*bootstrap)
            is_new = True
        else:
            is_new = False

        source_apt_conf = '/etc/apt/apt.conf'
        schroot_apt_conf = os.path.join(
                self['conf']['directory'], 'etc/apt/apt.conf')

        do_update = False
        if os.path.exists(source_apt_conf) and (
                not os.path.exists(schroot_apt_conf) or
                file(source_apt_conf).read() != file(schroot_apt_conf).read()):
            sudo('cp', source_apt_conf, schroot_apt_conf)
            do_update = True

        for source, location in self['sources'].items():
            source_path = os.path.join(self['conf']['directory'],
                'etc/apt/sources.list.d/', source +'.list')
            if not os.path.exists(source_path):
                create_root_file(source_path,
                    "deb %s %s %s\n" % (location['source'],
                        self['release'], source))
                do_update = True

        if do_update or not is_new:
            self.sudo(['apt-get', 'update'])
        if not is_new:
            self.sudo(['apt-get', 'dist-upgrade', '-y', '--auto-remove'])
        self.sudo(['apt-get', 'install', '-y', '--auto-remove'] +
                  self['packages'])


def load_schroots(config, kls=Schroot):
    """
        Builds the schroots indicated in the configuration file. A list of
        schroot instances will be returned of the type specified.
    """
    schroots = []
    for name in config["schroot"].keys():
        chroot = kls(config, name, config['source'],
            config.get('base-packages', []),
            config.get('http-proxy', None))
        schroots.append(chroot)
    return schroots
