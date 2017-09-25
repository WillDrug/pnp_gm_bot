from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class BaseCharacterParm:
    __basedice__ = 100
    __parmlist__ = 'dynamic'
    __cost__ = 0.1  # each point gives +10
    __referencename__ = 'Parm'

    char_id = Column(String, primary_key=True, ForeignKey('character.char_id'))
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

    char_id = Column(String, primary_key=True, ForeignKey('character.char_id'))
    name = Column(String, primary_key=True)
    apply_to = Column(String)
    apply_num = Column(Integer)
    flavourtext = Column(String)

    def __repr__(self):
        return "<%s(char_id='%s', name='%s', apply_to='%s', apply_num='%i', flavourtext='%s')>" % (
            self.__class__, self.char_id, self.name, self.apply_to, self.apply_num, self.flavourtext
        )
