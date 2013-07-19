import os

from mkschroot import create_root_file, execute, sudo


PERSONALITY = 'linux64' # Assume 64 bit for now
ARCH = { # Allow us to find the architecture from the personality name
    'linux64': 'amd64',
    'linux32': 'i386',
}


class Schroot(dict):
    def __init__(self, config, name, source, http_proxy):
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
        self['packages'] = self.get('packages', []) + \
            self.get('base-packages', [])
        for source, source_conf in self['sources'].items():
            if not source_conf.has_key('source'):
                source_conf['source'] = config['source']
        if self.has_key("variant"):
            for setup in ['config', 'copyfiles', 'fstab', 'nssdatabases']:
                if os.path.exists('/etc/schroot/%s/%s' % (self['variant'], setup)):
                    ensure("setup.%s" % setup, "%s/%s" % (self['variant'], setup))


    def update_conf_file(self):
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
        if not os.path.exists(self['conf']['directory']):
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
            self.sudo('apt-get', 'update')
        if not is_new:
            self.sudo('apt-get', 'dist-upgrade', '-y', '--auto-remove')
        self.sudo('apt-get', 'install', '-y', '--auto-remove',
            *self['packages'])


    def sudo(self, program, *args):
        """
            Execute the program as root in the schroot environment.
        """
        return execute('schroot', '--chroot', self.name, '--user', 'root',
                '--directory', '/home/', '--', program, *args)
