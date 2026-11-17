"""预约记录实体（对应实验五 E-R 图中的 appointment 表）。"""
from dataclasses import dataclass, field
from datetime import datetime
from itertools import count


@dataclass
class Appointment:
    """预约记录。

    Attributes:
        stu_id: 学生ID（外键，对应 users.user_id）。
        slot_id: 时段ID（外键，对应 slot.slot_id）。
        appt_id: 预约号（主键，模块内自增）。
        book_time: 下单时间。
        status: 状态，取值：已预约 / 已完成 / 已取消 / 缺考。
    """

    stu_id: int
    slot_id: int
    appt_id: int = field(default_factory=lambda: next(Appointment._id_gen))
    book_time: datetime = field(default_factory=datetime.now)
    status: str = "已预约"

    _id_gen = count(1)

    def cancel(self) -> None:
        """将状态置为已取消。"""
        self.status = "已取消"