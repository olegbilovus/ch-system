import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing_extensions import Annotated


class Base(DeclarativeBase):
    pass


str_nn = Annotated[str, mapped_column(nullable=False)]
int_nn = Annotated[int, mapped_column(nullable=False)]


@dataclass
class User(Base):
    __tablename__ = 'user_session'

    _keys_external_use = ['id', 'username', 'last_use']

    id: Mapped[str] = mapped_column(unique=True, default=str(uuid.uuid4()))
    sessionid: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str_nn]
    userprofileid: Mapped[int_nn]
    name: Mapped[str_nn]
    role: Mapped[int_nn]
    clanid: Mapped[int_nn]
    serverid: Mapped[int_nn]
    change_pw: Mapped[bool] = mapped_column(nullable=False)
    last_use: Mapped[datetime] = mapped_column(default=datetime.utcnow())

    def __repr__(self):
        return f'[id:{self.id},username:{self.username},userprofileid:{self.userprofileid},' \
               f'name:{self.name},role:{self.role},clanid:{self.clanid},serverid:{self.serverid}]'

    def get_external_data(self):
        data = {}
        for k, v in self.__dict__.items():
            if k in self._keys_external_use:
                data[k] = v

        return data
