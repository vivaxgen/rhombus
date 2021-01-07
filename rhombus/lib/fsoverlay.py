

# fsoverlay.py - file system overlay abstraction layer
# this library exports nd manages files straight from filesystem
# similar to static route, but looks for .rhoacl to get the metadata

from rhombus.lib.utils import random_string

from pyramid.path import AssetResolver

import os, yaml


# mount points for the fslayer
_MOUNTS = []


def fsomount(virtual_path, absolute_path):
    _MOUNTS.append(
        (os.path.normpath(virtual_path), os.path.normpath(absolute_path)) )


def mkranddir( parent_directory, userid ):
    d = FileOverlay(abspath = '%s/%s/' % (parent_directory, random_string(12)),
    	type = 'dir')
    d.add_permission(userid)
    d.create_directory()
    return d


def get_absmount(vpath):
	""" return mount_point """
	for virpath, abspath in _MOUNTS:
		if vpath.startswith( virpath ):
			return (virpath, abspath)
	return None

def get_virtmount(apath):
	""" return mount point """
	for virpath, abspath in _MOUNTS:
		if apath.startswith( abspath ):
			return (virpath, abspath)
	return None


def get_abspath(vpath, mp=None):
    """ return an absolute path from a virtual path """
    mp = mp or get_absmount(vpath)
    if mp:
        return mp[1] + vpath[len(mp[0]):]
    return None


def get_virtpath(apath, mp=None):
    """ return a virtual path from an absolute path """
    mp = mp or get_virtmount(apath)
    if mp:
    	return mp[0] + apath[len(mp[1]):]
    return None


def get_urlpath(abspath):
    return '/fso' + get_virtpath(abspath)


def return_as_response( rpath = None, vpath = None):
    pass

##
## .rhoacl is a YAML file, which provides authorization on the directory
## (more or less similar to apache .htaccess scheme)
##


class FileOverlay(object):

    def __init__(self, virtpath=None, abspath=None, type='file',
                        mount_point=None):
        """ mount_point: (virtual_path, absolute_path)
        """
        self.mount_point = None
        if mount_point:
            ar = AssetResolver()
            self.mount_point = (mount_point[0],
                            ar.resolve(mount_point[1]).abspath() + '/')
        if (virtpath and abspath):
        	raise RuntimeError('ERR - need only virtpath nor abspath')
        if virtpath:
            self.virtpath = os.path.normpath(virtpath)
            if mount_point is None:
                self.mount_point = get_absmount(self.virtpath)
            self.abspath = get_abspath(self.virtpath, self.mount_point)
        elif abspath:
            self.abspath = os.path.normpath(abspath)
            if mount_point is None:
                self.mount_point = get_virtmount(self.abspath)
            self.virtpath = get_virtpath(self.abspath, self.mount_point)
        else:
        	raise RuntimeERror('ERR - need either virtpath or abspath')
        self.parent = None
        self._meta = None
        self.type = type
        self.mimetype = None


    def create_directory(self):
        if self.type == 'dir':
            os.mkdir( self.abspath )
        else:
        	raise RuntimeError(
        		'ERR - can only create directory from directory type'
        	)
        with open(self.abspath + '/.rhoacl', 'w') as metafile:
        	yaml.dump(self.meta, metafile)
        # create .rhoauth as well


    @staticmethod
    def save(parentpath, filename, content, filetype='file/file',
                    mimetype=None, permanent = False):
        parent = FileOverlay.open( parentpath )
        if not parent:
            raise RuntimeError('Parent path not found: %s' % ppath)


    @staticmethod
    def openfile(virtpath, mode='r', mount_point=None):
        """ mount_point: (virtual_path, absolute_path )
        """
        if mode == 'r':
            fso_obj = FileOverlay( virtpath = virtpath,
                        mount_point = mount_point )
            return fso_obj

    @staticmethod
    def opendir(virtpath, mode='r'):
    	pass

    @property
    def urlpath(self):
        return get_urlpath(self.abspath)

    @property
    def meta(self):
        if self._meta is not None:
            return self._meta
        if self.type == 'file':
            # get the parent directory the reload .rhoacl
            rhoacl = os.path.dirname(self.abspath)
            with open(rhoacl + '/.rhoacl') as metafile:
                self._meta = yaml.load(metafile)
            return self._meta
        elif self.type == 'dir':
            # check whether this directory exists
            if os.path.exists(self.abspath):
                with open(self.abspath + '/.rhoacl') as metafile:
                    self._meta = yaml.load(metafile)
                return self._meta
            self._meta = {}
            return self._meta
        raise RuntimeError('ERR - unknown FileOverlay type')


    def add_permission(self, user):
    	if 'users' in self.meta:
    		self.meta['users'].append( user )
    	else:
    		self.meta['users'] = [ user ]


    def check_user_permission(self, user, mode=None):
    	if 'users' in self.meta and user in self.meta['users']:
    		return True
    	return False

    def check_groups_permission(self, groups, mode=None):
        pass


    def read(self):
        pass


    def write(self, data):
        pass

    @staticmethod
    def get_urlpath(abspath):
        return get_urlpath(abspath)
