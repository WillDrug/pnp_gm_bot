from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class BaseCharacterParm:
    __basedice__ = 100
    __parmlist__ = 'dynamic'
    __cost__ = 0.1  # each point gives +10
    __referencename__ = 'Parm'

    char_id = Column(String, primary_key=True)
    parm_name = Column(String, primary_key=True)
    parm_value = Column(Integer)
    bonus_sources = Column(String)
    penalty_sources = Column(String)

    def __repr__(self):
        return "<%s(char_id='%s', parm_name='%s', parm_value='%i', bonus_sources='%s', penalty_sources='%s')>" % (
            self.__class__, self.char_id, self.parm_name, self.parm_value, self.bonus_sources, self.penalty_sources
        )

    def calculate_bonus(self, influence):
        return (self.parm_value + influence) * 5



class BaseCharacterInfluence:
    __referencename__ = 'Influence'
    __cost__ = 50

    char_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    apply_to = Column(String)   # list
    apply_num = Column(Integer) # list
    flavourtext = Column(String)
    active = Column(Boolean)

    def __repr__(self):
        return "<%s(char_id='%s', name='%s', apply_to='%s', apply_num='%i', flavourtext='%s')>" % (
            self.__class__, self.char_id, self.name, self.apply_to, self.apply_num, self.flavourtext
        )

class BaseCharacterManeuver:
    __referencename__ = 'List'
    __cost__ = 40

    char_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    flavourtext = Column(String)

    def __repr__(self):
        return "<%s(char_id='%s', name='%s', flavourtext='%s')>" % (
            self.__class__, self.char_id, self.name, self.flavourtext
        )

class BaseCharacterResource:
    __referencename__ = 'Resource'

    char_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    max_value = Column(Integer)
    cur_value = Column(Integer)

    def __repr__(self):
        return "<%s(char_id='%s', name='%s', max_value='%i', cur_value='%i')>" % (
            self.__class__, self.char_id, self.name, self.max_value, self.cur_value
        )