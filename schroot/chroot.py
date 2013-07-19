import os

from schroot import create_root_file


PERSONALITY = 'linux64' # Assume 64 bit for now
ARCH = { # Allow us to find the architecture from the personality name
    'linux64': 'amd64',
    'linux32': 'i386',
}


class Schroot(dict):
    def __init__(self, config, name):
        """
            Build a chroot configuration by mixing the global and local configuration.
        """
        super(Schroot, self).__init__(conf={}, sources={})
        self.name = name
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

