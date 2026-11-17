"""统一返回结果对象（替代随意返回 None/dict，保证调用方处理显式化）。"""
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

CODE_OK = "0"


@dataclass(frozen=True)
class Result(Generic[T]):
    """业务操作统一返回结构。

    Attributes:
        success: 是否成功。
        code: 业务错误码，成功为 "0"（如 BANNED / FULL / TIME_WINDOW）。
        message: 面向用户的提示信息。
        data: 成功时的业务数据。
    """

    success: bool
    code: str
    message: str
    data: Optional[T] = None

    @staticmethod
    def ok(data: Optional[T] = None) -> "Result[T]":
        """构造成功结果。"""
        return Result(True, CODE_OK, "操作成功", data)

    @staticmethod
    def fail(code: str, message: str) -> "Result[T]":
        """构造失败结果。"""
        return Result(False, code, message, None)