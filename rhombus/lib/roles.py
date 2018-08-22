
SYSADM = '~r|system-adm'
SYSVIEW = '~r|system-viewer'
DATAADM = '~r|data-adm'
DATAVIEW = '~r|data-viewer'
PUBLIC = '~r|public'
USER = '~r|user'
GUEST = '~r|guest'

EK_CREATE = '~r|ek|create'
EK_MODIFY = '~r|ek|modify'
EK_VIEW = '~r|ek|view'
EK_DELETE = '~r|ek|delete'

USERCLASS_CREATE = '~r|userclass|create'
USERCLASS_MODIFY = '~r|userclass|modify'
USERCLASS_VIEW = '~r|userclass|view'
USERCLASS_DELETE = '~r|userclass|delete'

USER_CREATE = '~r|user|create'
USER_MODIFY = '~r|user|modify'
USER_VIEW = '~r|user|view'
USER_DELETE = '~r|user|delete'

GROUP_CREATE = '~r|group|create'
GROUP_MODIFY = '~r|group|modify'
GROUP_VIEW = '~r|group|view'
GROUP_DELETE = '~r|group|delete'
GROUP_ADDUSER = '~r|group|add-user'
GROUP_DELUSER = '~r|group|del-user'


def is_sysadm(user):

    return user.has_roles(SYSADM)

    raise NotImplementedError('Need to think about this')
    return True
