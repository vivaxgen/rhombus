
from .core import *
from .ek import EK
from sqlalchemy.orm import exc


class DictEmulator(object):

    def __init__(self, getitem_func, setitem_func):
        self._getitem_ = getitem_func
        self._setitem_ = setitem_func
        self._delitem_ = delitem_func

    def __getitem__(self, key):
        return self._getitem_(key)

    def __setitem__(self, key, value):
        self._setitem_(key, value)

    def __delitem__(self, key):
        self._delitem_(key)


class EnumDataDict(DictEmulator):

    def __init__(self, instance, attrname):
        self._inst = instance
        self._attrname = attrname

    def __getitem__(self, key):
        key_id = EK._id( getattr(self._inst, self._attrname),
                        dbsession = object_session(self._inst) )

    

class EnumDataMixIn(BaseMixIn):
    """ EnumDataMixIn

        This is common structure for EnumKey-paired data item.
    """

    @declared_attr
    def cat_id(cls):
        return Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    @declared_attr
    def cat(cls):
        return EK.proxy('cat_id')
    """ data enumerated category """

    @declared_attr
    def val_id(cls):
        return Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    def val(cls):
        return EK.proxy('val_id')
    """ data enumerated value """

    @classmethod
    def proxy(cls, attrname):
        def _getter(inst):
            return EnumDataDict(inst)
        def _setter(inst):
            raise RuntimeError("Dict-based class cannot be set")
        return property(_getter, _setter) 


class StringDataMixIn(BaseMixIn):
    """ StringDataMixIn

        This is common structure for EnumKey-categorical string data.
    """

    string_length = 255
    iattr = '__stringdata_interface'

    def __init__(self, cat_id, val):
        self.cat_id = cat_id
        self.val = val

    @declared_attr
    def cat_id(cls):
        return Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    @declared_attr
    def cat(cls):
        return EK.proxy('cat_id')
    """ data enumerated category """

    @declared_attr
    def val(cls):
        return Column(types.String(cls.string_length), nullable=False)

    @classmethod
    def interface(cls, attrname):
        """ attrname is the attribute in this class that pointing to the other object
        """
        def _getter(instance):
            if not hasattr(instance, cls.iattr):
                setattr(instance, cls.iattr, DictInterface( cls, instance.id, attrname ))
            return getattr(instance, cls.iattr)

        return property(_getter)


class DictInterface(object):

    def __init__(self, mixin, instance_id, attrname ):
        self.mixin = mixin
        self.instance_id = instance_id
        self.attrname = attrname

    def getobj(self, id):
        try:
            return self.mixin.query().filter( self.mixin.cat_id == id, 
                        getattr(self.mixin, self.attrname) == self.instance_id ).one()
        except exc.NoResultFound:
            raise KeyError('key not found')

    def __getitem__(self, key):
        ek_id = EK.getid( key )
        obj = self.getobj(ek_id)
        return obj.val

    def __setitem__(self, key, value):
        ek_id = EK.getid( key )
        try:
            obj = self.getobj(ek_id)
            obj.val = value
        except KeyError:
            obj = self.mixin(cat_id = ek_id, val = value)
            setattr(obj, self.attrname, self.instance_id)
            dbsession.add( obj )

    def get(self, key, default_value):
        try:
            return self[key]
        except KeyError:
            return default_value
        
