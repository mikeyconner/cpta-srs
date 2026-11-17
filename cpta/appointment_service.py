"""预约管理模块核心实现（实验四模块划分：预约管理模块 / AppointmentService）。"""
from datetime import datetime

from .appointment import Appointment
from .result import Result
from .services import (AppointmentRepository, NotificationService,
                       ScheduleService, UserService)

# 取消预约允许的时间窗口（小时），对应 FR-005
CANCEL_WINDOW_HOURS = 24


class AppointmentService:
    """预约管理模块对外服务。

    实现要点（可追溯至实验二 SRS / 实验五详细设计）：
        1. book()：封禁校验（IJ-01）→ 原子扣名额（IJ-04）→ 写入预约记录
           → 异步通知（IJ-09）；前三步生产环境处于同一事务，任一失败整体回滚；
        2. 名额不超卖由 deduct_slot 的原子 UPDATE 保证（NFR-002）；
        3. cancel() 执行 24 小时窗口校验（FR-005）。
    """

    def __init__(self, user_service: UserService,
                 schedule_service: ScheduleService,
                 notification_service: NotificationService,
                 repository: AppointmentRepository) -> None:
        """构造函数注入全部依赖，模块间仅通过接口交互。"""
        self._user_service = user_service
        self._schedule_service = schedule_service
        self._notification_service = notification_service
        self._repository = repository

    def book(self, stu_id: int, slot_id: int) -> Result[Appointment]:
        """预约体测（核心用例，对应实验三用例1、实验五时序图）。

        Args:
            stu_id: 学生ID。
            slot_id: 时段ID。

        Returns:
            预约结果，成功时 data 为预约记录。
        """
        # 步骤1：爽约封禁校验（FR-012 / IJ-01）
        if self._user_service.check_ban(stu_id):
            return Result.fail("BANNED", "账号处于封禁期，禁止预约")
        # 步骤2：原子扣减名额（FR-004 / IJ-04），失败即名额不足
        if not self._schedule_service.deduct_slot(slot_id):
            return Result.fail("FULL", "该时段已约满，请选择其他时段")
        # 步骤3：写入预约记录（与步骤2同一事务，生产环境保证）
        appointment = Appointment(stu_id=stu_id, slot_id=slot_id)
        self._repository.save(appointment)
        # 步骤4：异步发送预约成功通知（FR-014 / IJ-09），不阻塞主流程
        self._notification_service.send_async(
            stu_id, "APPT_SUCCESS", str(appointment.appt_id))
        return Result.ok(appointment)

    def cancel(self, appt_id: int) -> Result[None]:
        """取消预约（FR-005：开测前24小时外可取消并释放名额）。

        Args:
            appt_id: 预约号。

        Returns:
            取消结果。
        """
        appointment = self._repository.find_by_id(appt_id)
        if appointment is None:
            return Result.fail("NOT_FOUND", "预约记录不存在")
        if appointment.status != "已预约":
            return Result.fail("BAD_STATE", "当前状态不允许取消")
        # 24小时窗口校验（FR-005）：开测前24小时内不可取消
        slot_start = self._schedule_service.get_slot_start_time(appointment.slot_id)
        if slot_start.timestamp() - CANCEL_WINDOW_HOURS * 3600 < datetime.now().timestamp():
            return Result.fail("TIME_WINDOW", "开测前24小时内不可取消")
        appointment.cancel()
        self._repository.update(appointment)
        self._schedule_service.release_slot(appointment.slot_id)
        self._notification_service.send_async(
            appointment.stu_id, "APPT_CANCEL", str(appt_id))
        return Result.ok()