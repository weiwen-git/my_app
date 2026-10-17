"""生成 bcrypt 哈希，用于 .env 的 WB_PASSWORD_HASH。

用法：python backend/scripts/make-password.py
"""

from __future__ import annotations

import getpass

import bcrypt


def main() -> None:
    pwd = getpass.getpass("输入新密码：")
    if len(pwd) < 6:
        print("[error] 密码至少 6 位")
        return
    if pwd != getpass.getpass("再输入一次："):
        print("[error] 两次输入不一致")
        return

    hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print("\n把下面这行写进 backend/.env（替换 WB_PASSWORD_HASH）：\n")
    print(f"WB_PASSWORD_HASH={hashed}")
    print("\n改完重启服务生效。")


if __name__ == "__main__":
    main()
