
# exception class

class SysError( RuntimeError ):
    pass

class UserError( RuntimeError ):
    pass

class DBError( RuntimeError ):
    pass

class AuthError( RuntimeError ):
    pass


