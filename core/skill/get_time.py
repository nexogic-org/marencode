from datetime import datetime
import time

def get_current_time() -> str:
    """
    获取当前系统时间，包含年月日、时分秒和星期几
    """
    now = datetime.now()
    week_days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    week_day = week_days[now.weekday()]
    return now.strftime(f"%Y-%m-%d %H:%M:%S {week_day}")

def get_timestamp() -> float:
    """获取当前时间戳"""
    return time.time()
