from typing import List, Optional

from sqlalchemy import Column, Date, Enum, ForeignKey, Index, Integer, Text, UniqueConstraint, text, create_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship, sessionmaker
from sqlalchemy.orm.base import Mapped

Base = declarative_base()

engine = create_engine('sqlite:///squiidvault.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency function that provides a SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Alliances(Base):
    __tablename__ = 'alliances'

    name = mapped_column(Text, nullable=False, unique=True)
    status = mapped_column(Enum('active', 'inactive'), nullable=False, server_default=text("'active'"))
    id = mapped_column(Integer, primary_key=True)
    description = mapped_column(Text)

    alliance_sets_map: Mapped[List['AllianceSetsMap']] = relationship('AllianceSetsMap', uselist=True, back_populates='alliance')


class Config(Base):
    __tablename__ = 'config'

    key = mapped_column(Text, primary_key=True)
    value = mapped_column(Integer, unique=True)


class Enums(Base):
    __tablename__ = 'enums'
    __table_args__ = (
        UniqueConstraint('enum_type', 'enum_key'),
    )

    enum_type = mapped_column(Text, nullable=False)
    enum_key = mapped_column(Text, nullable=False)
    enum_value = mapped_column(Text, nullable=False)
    id = mapped_column(Integer, primary_key=True)


class Sets(Base):
    __tablename__ = 'sets'

    name = mapped_column(Text, nullable=False, unique=True)
    type = mapped_column(Enum('active', 'extinct', 'system'), nullable=False, server_default=text("'active'"))
    id = mapped_column(Integer, primary_key=True)
    description = mapped_column(Text)
    emoji = mapped_column(Text)

    alliance_sets_map: Mapped[List['AllianceSetsMap']] = relationship('AllianceSetsMap', uselist=True, back_populates='set')
    members: Mapped[List['Members']] = relationship('Members', uselist=True, back_populates='set')
    set_allies_map: Mapped[List['SetAlliesMap']] = relationship('SetAlliesMap', uselist=True, foreign_keys='[SetAlliesMap.ally_id]', back_populates='ally')
    set_allies_map_: Mapped[List['SetAlliesMap']] = relationship('SetAlliesMap', uselist=True, foreign_keys='[SetAlliesMap.set_id]', back_populates='set')
    set_enemies_map: Mapped[List['SetEnemiesMap']] = relationship('SetEnemiesMap', uselist=True, foreign_keys='[SetEnemiesMap.enemy_id]', back_populates='enemy')
    set_enemies_map_: Mapped[List['SetEnemiesMap']] = relationship('SetEnemiesMap', uselist=True, foreign_keys='[SetEnemiesMap.set_id]', back_populates='set')


class AllianceSetsMap(Base):
    __tablename__ = 'alliance_sets_map'
    __table_args__ = (
        UniqueConstraint('alliance_id', 'set_id'),
    )

    alliance_id = mapped_column(ForeignKey('alliances.id', ondelete='CASCADE'), nullable=False)
    set_id = mapped_column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    id = mapped_column(Integer, primary_key=True)

    alliance: Mapped['Alliances'] = relationship('Alliances', back_populates='alliance_sets_map')
    set: Mapped['Sets'] = relationship('Sets', back_populates='alliance_sets_map')


class Members(Base):
    __tablename__ = 'members'
    __table_args__ = (
        Index('idx_members_set_id', 'set_id'),
    )

    name = mapped_column(Text, nullable=False)
    status = mapped_column(Enum('dead', 'alive', 'locked_up', 'unknown'), nullable=False)
    id = mapped_column(Integer, primary_key=True)
    description = mapped_column(Text)
    release_date = mapped_column(Date)
    release_date_approx = mapped_column(Text, server_default=text("'unknown'"))
    death_date = mapped_column(Date)
    death_date_approx = mapped_column(Text, server_default=text("'unknown'"))
    set_id = mapped_column(ForeignKey('sets.id', ondelete='SET NULL'))
    alliance_id = mapped_column(Integer, server_default=text('NULL'))

    set: Mapped[Optional['Sets']] = relationship('Sets', back_populates='members')
    assists: Mapped[List['Assists']] = relationship('Assists', uselist=True, foreign_keys='[Assists.shooter_id]', back_populates='shooter')
    assists_: Mapped[List['Assists']] = relationship('Assists', uselist=True, foreign_keys='[Assists.victim_id]', back_populates='victim')
    murders: Mapped[List['Murders']] = relationship('Murders', uselist=True, foreign_keys='[Murders.shooter_id]', back_populates='shooter')
    murders_: Mapped['Murders'] = relationship('Murders', uselist=False, foreign_keys='[Murders.victim_id]', back_populates='victim')
    shootings: Mapped[List['Shootings']] = relationship('Shootings', uselist=True, foreign_keys='[Shootings.shooter_id]', back_populates='shooter')
    shootings_: Mapped[List['Shootings']] = relationship('Shootings', uselist=True, foreign_keys='[Shootings.victim_id]', back_populates='victim')


class SetAlliesMap(Base):
    __tablename__ = 'set_allies_map'
    __table_args__ = (
        UniqueConstraint('set_id', 'ally_id'),
    )

    set_id = mapped_column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    ally_id = mapped_column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    id = mapped_column(Integer, primary_key=True)

    ally: Mapped['Sets'] = relationship('Sets', foreign_keys=[ally_id], back_populates='set_allies_map')
    set: Mapped['Sets'] = relationship('Sets', foreign_keys=[set_id], back_populates='set_allies_map_')


class SetEnemiesMap(Base):
    __tablename__ = 'set_enemies_map'
    __table_args__ = (
        UniqueConstraint('set_id', 'enemy_id'),
    )

    set_id = mapped_column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    enemy_id = mapped_column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    id = mapped_column(Integer, primary_key=True)

    enemy: Mapped['Sets'] = relationship('Sets', foreign_keys=[enemy_id], back_populates='set_enemies_map')
    set: Mapped['Sets'] = relationship('Sets', foreign_keys=[set_id], back_populates='set_enemies_map_')


class Assists(Base):
    __tablename__ = 'assists'

    shooter_id = mapped_column(ForeignKey('members.id'), nullable=False)
    victim_id = mapped_column(ForeignKey('members.id'), nullable=False)
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date)
    date_approx = mapped_column(Text, server_default=text("'unknown'"))

    shooter: Mapped['Members'] = relationship('Members', foreign_keys=[shooter_id], back_populates='assists')
    victim: Mapped['Members'] = relationship('Members', foreign_keys=[victim_id], back_populates='assists_')


class Murders(Base):
    __tablename__ = 'murders'

    shooter_id = mapped_column(ForeignKey('members.id'), nullable=False)
    victim_id = mapped_column(ForeignKey('members.id'), nullable=False, unique=True)
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date)
    date_approx = mapped_column(Text, server_default=text("'unknown'"))

    shooter: Mapped['Members'] = relationship('Members', foreign_keys=[shooter_id], back_populates='murders')
    victim: Mapped['Members'] = relationship('Members', foreign_keys=[victim_id], back_populates='murders_')


class Shootings(Base):
    __tablename__ = 'shootings'

    shooter_id = mapped_column(ForeignKey('members.id'), nullable=False)
    victim_id = mapped_column(ForeignKey('members.id'), nullable=False)
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date)
    date_approx = mapped_column(Text, server_default=text("'unknown'"))

    shooter: Mapped['Members'] = relationship('Members', foreign_keys=[shooter_id], back_populates='shootings')
    victim: Mapped['Members'] = relationship('Members', foreign_keys=[victim_id], back_populates='shootings_')
