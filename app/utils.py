import logging
from datetime import datetime
from ipaddress import ip_address
from struct import unpack
from typing import Any

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from tqdm import tqdm

from app.models import IPData


def int_ip_to_str(ip_int: int) -> str | None:
    """整数 IP 转换为字符串"""
    try:
        return str(ip_address(ip_int))
    except Exception as e:
        logging.info(f"无效的整数 IP 地址 {ip_int}: {e}")
        return None


def str_ip_to_int(ip_str: str) -> int | None:
    """字符串 IP 转换为整数"""
    try:
        return int(ip_address(ip_str))
    except Exception as e:
        logging.info(f"无效的字符串 IP 地址 {ip_str}: {e}")
        return None


def gbk_bytes_to_utf8(gbk_bytes: bytes) -> str:
    """将 GBK 编码的字节流转换为 UTF-8 字符串"""
    try:
        return gbk_bytes.decode("gbk", errors="replace")
    except UnicodeDecodeError as e:
        logging.info(f"解码错误: {e}")
        # # 处理末尾字节损坏的特殊情况
        if gbk_bytes.endswith(b"\x96"):
            try:
                return gbk_bytes[:-1].decode("gbk", errors="replace") + "?"
            except UnicodeDecodeError:
                pass
        return "未知地区"


class IPLoader:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.db_buffer = open(file_name, "rb")
        self.idx_start, self.idx_end, self.idx_count = self._get_index()

    def _get_index(self) -> tuple[int, int, int]:
        """读取索引范围并计算记录数"""
        self.db_buffer.seek(0)
        start, end = unpack("<II", self.db_buffer.read(8))
        return start, end, (end - start) // 7 + 1

    def _read_uint32(self, offset: int) -> int:
        """从指定偏移读取32位无符号整数"""
        self.db_buffer.seek(offset)
        return unpack("<I", self.db_buffer.read(4))[0]

    def _read_offset(self, offset: int) -> int:
        """读取3字节偏移量"""
        self.db_buffer.seek(offset)
        return unpack("<I", self.db_buffer.read(3) + b"\x00")[0]

    def _read_string(self, offset: int) -> bytes:
        """读取以\0结尾的原始字节流"""
        if offset == 0:
            return b""
        self.db_buffer.seek(offset)
        buffer = bytearray()
        while (byte := self.db_buffer.read(1)) != b"\x00":
            if not byte:
                break
            buffer.extend(byte)
        return bytes(buffer)

    def _get_record(self, offset: int) -> tuple[bytes, bytes]:
        """解析IP记录信息"""
        self.db_buffer.seek(offset)
        match ord(self.db_buffer.read(1)):
            case 1:
                new_offset = self._read_offset(offset + 1)
                return self._parse_record(new_offset)
            case 2:
                location = self._read_string(self._read_offset(offset + 1))
                info = self._read_string(offset + 4)
                return location, info
            case _:
                self.db_buffer.seek(offset)
                location = self._read_string(offset)
                info = self._read_string(offset + len(location) + 1)
                return location, info

    def _parse_record(self, offset: int) -> tuple[bytes, bytes]:
        """处理重定向记录"""
        self.db_buffer.seek(offset)
        if (ord(self.db_buffer.read(1))) == 2:
            location = self._read_string(self._read_offset(offset + 1))
            info = self._read_string(offset + 4)
        else:
            location = self._read_string(offset)
            info = self._read_string(offset + len(location) + 1)
        return location, info

    def _binary_search(self, ip: int, low: int, high: int) -> int:
        """二分查找IP索引位置"""
        while high - low > 1:
            mid = (low + high) // 2
            mid_ip = self._read_uint32(self.idx_start + mid * 7)
            if ip < mid_ip:
                high = mid
            else:
                low = mid
        return low

    def get_ip_info(self, ip_str: str) -> dict[str, Any]:
        """获取IP地址完整信息"""
        result = {"code": 1, "data": {"ip": ip_str, "location": "", "info": ""}}
        if (ip := str_ip_to_int(ip_str)) is None:
            result["data"]["info"] = "非法IP地址"
            return result

        index = self._binary_search(ip, 0, self.idx_count - 1)
        record_offset = self._read_offset(self.idx_start + index * 7 + 4)
        location, info = self._get_record(record_offset + 4)

        result.update({"code": 0, "data": {"location": gbk_bytes_to_utf8(location), "info": gbk_bytes_to_utf8(info)}})
        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_buffer.close()

    def __del__(self):
        self.db_buffer.close()


def dat_to_database(db: SQLAlchemy):
    """将 qqwry.dat 文件导入到 SQLite 数据库"""
    records = []

    with IPLoader(current_app.config["QQWRY_DAT_PATH"]) as loader:
        total = loader.idx_count

        print(f"开始解析 DAT 文件数据，共有 {total} 条记录")

        for i in tqdm(range(total), desc="正在解析数据"):
            # 读取当前记录的 IP 和偏移量
            offset = loader.idx_start + i * 7
            ip_start_num = loader._read_uint32(offset)

            # 计算结束 IP
            if i < total - 1:
                ip_end_num = loader._read_uint32(offset + 7) - 1
            else:
                ip_end_num = 0xFFFFFFFF

            # 获取地区信息
            record_offset = loader._read_offset(offset + 4)
            location, info = loader._get_record(record_offset + 4)
            location = "未知" if location == "IANA" else location
            info = "未知" if info == "CZ88.NET" else info

            records.append(
                {
                    "ip_start_num": ip_start_num,
                    "ip_end_num": ip_end_num,
                    "location": gbk_bytes_to_utf8(location),
                    "info": gbk_bytes_to_utf8(info),
                }
            )

        print("\n数据解析完成，正在导入数据库...")

    # 批量插入数据库
    db.session.bulk_insert_mappings(IPData, records)
    db.session.commit()
    print(f"成功导入 {len(records)} 条记录到数据库")


def inject_env_vars():
    now = datetime.now()
    env_vars = {
        "DATA_UPDATED_DATE": current_app.config.get("DATA_UPDATED_DATE"),
        "TIME": {
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
        },
    }

    return {"env_vars": env_vars}
