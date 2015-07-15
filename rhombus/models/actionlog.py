
from .core import *
from .ek import *
from .user import *

from datetime import datetime
import json

class ActionLog(Base):
    """ Action Log """

    __tablename__ = 'actionlogs' 
    id = Column(types.Integer, Sequence('actionlog_seqid', optional=True),
            primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False,
            default=get_userid)
    action_id = Column(types.Integer, ForeignKey('eks.id'))
    status = Column(types.String(1), default='P')
    objs = Column(types.String(128))
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    def message(self):
        fmt_objects = json.loads( self.objs )
        return str(User.get(self.user_id)) + (EK.get(self.action_id).desc[2:] % fmt_objects)

    def timestamp(self):
        current_time = datetime.now()
        delta_time = current_time - self.stamp
        if delta_time.days > 0:
            if delta_time.days > 30:
                return '%d month(s) ago' % (delta_time.days / 30)
            elif delta_time.days > 7:
                return '%d week(s) ago' % (delta_time.days / 7)
            else:
                return '%d day(s) ago' % delta_time.days

        if delta_time.seconds > 3600:
            return '%d hour(s) ago' % (delta_time.seconds / 3600)
        elif delta_time.seconds > 60:
            return '%d minute(s) ago' % (delta_time.seconds / 60)
        else:
            return '%d second(s) ago' % delta_time.seconds

        

    @staticmethod
    def add(action_id, *args, **kwargs):
        actionlog = ActionLog()
        actionlog.action_id = action_id
        actionlog.objs = json.dumps( args )
        dbsession.add(actionlog)

        if kwargs:
            dbsession.flush()

        for k in kwargs:
            if k == 'affected_user_id':
                actionlog.status = 'U'
                UserActionLog.add(user_id = get_userid(), actionlog_id = actionlog.id)
                if get_userid() != kwargs[k]:
                    UserActionLog.add(user_id = kwargs[k], actionlog_id = actionlog.id)
                
            elif k == 'affected_group_id':
                group = Group.get( kwargs[k] )
                for u in group.users:
                    UserActionLog.add( user_id = u.id, actionlog_id = actionlog.id )
                actionlog.status = 'U'

            else:
                raise RuntimeError('ActionLog.add(): unregconized keyword arguments %s' % k)


class UserActionLog(Base):
    """ User-targetted Action Log """

    __tablename__ = 'useractionlogs'
    id = Column(types.Integer, Sequence('useractionlog_seqid', optional=True),
            primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    actionlog_id = Column(types.Integer, ForeignKey('actionlogs.id'), nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    __table_args__ = ( UniqueConstraint('user_id', 'actionlog_id'), {} )

    actionlog = relationship(ActionLog, uselist=False)

    def message(self):
        return self.actionlog.message()

    def timestamp(self):
        return self.actionlog.timestamp()

    @staticmethod
    def add(user_id, actionlog_id):
        dbsession.add( UserActionLog(user_id = user_id, actionlog_id = actionlog_id) )


