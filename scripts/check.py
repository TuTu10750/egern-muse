#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check.py —— 规则集自检：YAML 合法性 + 域名匹配行为

用法:
    python3 scripts/check.py

检查项:
    1. 所有 Rules/*.yaml 能被解析，键名在 Egern 支持列表内
    2. 值必须是字符串列表，且域名格式合法、无重复
    3. 按 Egern 的后缀匹配语义（label 边界）跑一组命中/不命中用例
       —— 重点防 "notmeta.ai" 被误判为命中 "meta.ai"
"""
import glob
import os
import sys

import yaml

# Egern 规则集支持的键（来自官方规则文档）
ALLOWED_KEYS = {
    "no_resolve", "domain_set", "domain_suffix_set", "domain_keyword_set",
    "domain_wildcard_set", "ip_cidr_set", "ip_cidr6_set", "asn_set",
    "url_regex_set", "user_agent_set", "dest_port_set", "geoip_set",
}
LIST_KEYS = ALLOWED_KEYS - {"no_resolve"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERRORS = []


def err(msg):
    ERRORS.append(msg)
    print(f"  [x] {msg}")


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_file(path):
    name = os.path.relpath(path, ROOT)
    print(f"\n[文件] {name}")
    try:
        data = load(path)
    except yaml.YAMLError as e:
        err(f"YAML 解析失败: {e}")
        return None

    if not isinstance(data, dict):
        err("根节点必须是映射")
        return None

    for k, v in data.items():
        if k not in ALLOWED_KEYS:
            err(f"不支持的键: {k}")
            continue
        if k == "no_resolve":
            if not isinstance(v, bool):
                err(f"no_resolve 必须是布尔值，实际: {type(v).__name__}")
            continue
        if not isinstance(v, list):
            err(f"{k} 必须是列表")
            continue
        seen = set()
        for item in v:
            if not isinstance(item, str):
                err(f"{k} 中的值必须是字符串: {item!r}")
                continue
            if item != item.strip() or " " in item:
                err(f"{k} 中的值含空格: {item!r}")
            if item.lower() in seen:
                err(f"{k} 重复值: {item}")
            seen.add(item.lower())
            if k.startswith("domain"):
                if item.startswith(("http://", "https://", "/")):
                    err(f"{k} 不应带协议或路径: {item}")
    print(f"  [✓] 结构合法，共 {sum(len(v) for k, v in data.items() if k in LIST_KEYS)} 条规则")
    return data


def suffix_match(host: str, domain: str) -> bool:
    """Egern 后缀匹配语义：等于该域名，或以 '.'+域名 结尾。"""
    host, domain = host.lower().rstrip("."), domain.lower().strip(".")
    return host == domain or host.endswith("." + domain)


def run_cases(data, cases, label):
    print(f"\n[匹配测试] {label}")
    suffixes = data.get("domain_suffix_set") or []
    exact = set(d.lower() for d in (data.get("domain_set") or []))
    ok = 0
    for host, expect in cases:
        hit = host.lower() in exact or any(suffix_match(host, d) for d in suffixes)
        flag = "✓" if hit == expect else "✗"
        if hit == expect:
            ok += 1
        else:
            err(f"{label}: {host} 期望 {'命中' if expect else '不命中'}，实际相反")
        print(f"  [{flag}] {host:<28} {'命中' if hit else '不命中'}")
    print(f"  {ok}/{len(cases)} 通过")


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "Rules", "*.yaml")))
    if not files:
        print("没有找到 Rules/*.yaml")
        return 1

    loaded = {}
    for p in files:
        d = check_file(p)
        if d:
            loaded[os.path.basename(p)] = d

    slim = loaded.get("MetaMuse.yaml")
    if slim:
        run_cases(slim, [
            ("muse.meta.com", True),
            ("www.muse.meta.com", True),
            ("meta.ai", True),
            ("www.meta.ai", True),
            ("api.meta.ai", True),
            ("ai.meta.com", True),
            ("facebook.com", False),
            ("notmeta.ai", False),          # 关键：不能被 "meta.ai" 误吞
            ("meta.ai.evil.com", False),    # 关键：后缀必须在 label 边界
            ("muse.meta.com.cn", False),
        ], "MetaMuse.yaml 精简版")

    full = loaded.get("MetaMuse-Full.yaml")
    if full:
        run_cases(full, [
            ("scontent.xx.fbcdn.net", True),
            ("static.xx.fbsbx.com", True),
            ("graph.facebook.com", True),
            ("muse.meta.com", True),
            ("www.meta.ai", True),
            ("instagram.com", False),       # 只放 CDN，不放主站
        ], "MetaMuse-Full.yaml 完整版")

    print("\n" + "=" * 52)
    if ERRORS:
        print(f"检查未通过，共 {len(ERRORS)} 个问题")
        return 1
    print("全部检查通过 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
