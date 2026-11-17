"""模块独立运行演示：以内存桩（Stub）实现各依赖接口。

覆盖 6 个场景，验证预约管理模块可单独运行且正常/异常行为均符合设计。
"""
from datetime import datetime, timedelta
from typing import Optional

from .appointment import Appointment
from .appointment_service import AppointmentService
from .result import Result
from .services import (AppointmentRepository, NotificationService,
                       ScheduleService, UserService)


class _StubUserService(UserService):
    """用户模块内存桩：学号 9999 模拟封禁学生。"""

    def check_ban(self, stu_id: int) -> bool:
        return stu_id == 9999


class _StubScheduleService(ScheduleService):
    """排期模块内存桩：模拟数据库原子扣减（真实环境靠 UPDATE 行锁）。"""

    def __init__(self) -> None:
        self._slots: dict[int, list] = {}      # slot_id -> [capacity, booked]
        self._start: dict[int, datetime] = {}

    def add_slot(self, slot_id: int, capacity: int, start: datetime) -> None:
        """演示辅助方法：登记一个时段。"""
        self._slots[slot_id] = [capacity, 0]
        self._start[slot_id] = start

    def deduct_slot(self, slot_id: int) -> bool:
        capacity, booked = self._slots[slot_id]
        if booked >= capacity:
            return False
        self._slots[slot_id][1] += 1
        return True

    def release_slot(self, slot_id: int) -> None:
        if self._slots[slot_id][1] > 0:
            self._slots[slot_id][1] -= 1

    def get_slot_start_time(self, slot_id: int) -> datetime:
        return self._start[slot_id]


class _StubNotificationService(NotificationService):
    """通知模块内存桩：打印代替真实发送。"""

    def send_async(self, user_id: int, template_code: str, params: str) -> None:
        print(f"  [通知] userId={user_id} 模板={template_code} 参数={params}")


class _StubRepository(AppointmentRepository):
    """持久层内存桩。"""

    def __init__(self) -> None:
        self._store: dict[int, Appointment] = {}

    def save(self, appointment: Appointment) -> None:
        self._store[appointment.appt_id] = appointment

    def update(self, appointment: Appointment) -> None:
        self._store[appointment.appt_id] = appointment

    def find_by_id(self, appt_id: int) -> Optional[Appointment]:
        return self._store.get(appt_id)


def _show(title: str, result: Result) -> None:
    print(f"===== {title} =====")
    print(f"  {result}")


def main() -> None:
    """运行 6 个测试场景。"""
    now = datetime.now()
    schedule = _StubScheduleService()
    schedule.add_slot(1001, capacity=2, start=now + timedelta(hours=48))
    schedule.add_slot(1002, capacity=1, start=now + timedelta(hours=10))

    service = AppointmentService(
        _StubUserService(), schedule, _StubNotificationService(), _StubRepository())

    _show("场景1：正常预约", service.book(2024101708, 1001))
    _show("场景1：正常预约", service.book(2024101709, 1001))
    _show("场景2：名额已满（异常）", service.book(2024101710, 1001))
    _show("场景3：封禁学生预约（异常）", service.book(9999, 1002))
    _show("场景4：24小时外取消（正常）", service.cancel(1))
    _show("场景5：重复取消（异常）", service.cancel(1))
    service.book(2024101711, 1002)
    _show("场景6：24小时内取消（异常）", service.cancel(3))


if __name__ == "__main__":
    main()