"""模块间依赖接口（对应实验四模块间接口定义 IJ-01 / IJ-04 / IJ-05 / IJ-09）。

本模块只依赖这里的抽象接口，不依赖用户、排期、通知模块的任何具体实现。
"""
from abc import ABC, abstractmethod
from datetime import datetime


class UserService(ABC):
    """用户管理模块对外接口（IJ-01）。"""

    @abstractmethod
    def check_ban(self, stu_id: int) -> bool:
        """查询学生账号是否处于爽约封禁期（FR-012）。

        Args:
            stu_id: 学生ID。

        Returns:
            True 表示封禁中，False 表示可预约。
        """


class ScheduleService(ABC):
    """排期与场次管理模块对外接口（IJ-04 / IJ-05）。"""

    @abstractmethod
    def deduct_slot(self, slot_id: int) -> bool:
        """原子扣减时段名额（FR-004，防超卖 NFR-002）。

        生产环境实现为 UPDATE slot SET booked = booked + 1
        WHERE slot_id = %s AND booked < capacity，影响 0 行即返回 False。

        Args:
            slot_id: 时段ID。

        Returns:
            True 扣减成功；False 名额不足。
        """

    @abstractmethod
    def release_slot(self, slot_id: int) -> None:
        """释放时段名额（FR-005，取消预约时调用）。

        Args:
            slot_id: 时段ID。
        """

    @abstractmethod
    def get_slot_start_time(self, slot_id: int) -> datetime:
        """查询时段开始时间，用于取消预约的 24 小时窗口校验（FR-005）。

        Args:
            slot_id: 时段ID。

        Returns:
            时段开始时间。
        """


class NotificationService(ABC):
    """通知服务模块对外接口（IJ-09，异步发送）。"""

    @abstractmethod
    def send_async(self, user_id: int, template_code: str, params: str) -> None:
        """异步发送站内通知（FR-014），失败入队重发，不阻塞主流程。

        Args:
            user_id: 接收人ID。
            template_code: 消息模板编码，如 APPT_SUCCESS / APPT_CANCEL。
            params: 模板参数（如预约号）。
        """


class AppointmentRepository(ABC):
    """预约记录持久化接口（数据访问层，对应 appointment 表）。"""

    @abstractmethod
    def save(self, appointment: "Appointment") -> None: ...

    @abstractmethod
    def update(self, appointment: "Appointment") -> None: ...

    @abstractmethod
    def find_by_id(self, appt_id: int) -> "Appointment | None": ...