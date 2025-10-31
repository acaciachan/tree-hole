# -*- coding: utf-8 -*-
"""
Bilibili Follower Display Plugin for MCDR
Version: 2.1
Author: 通义千问/小豆
功能：通过假人显示B站UP主粉丝数，支持MID修改/定时自动更新不可用！
配置文件：bfanconfig.json
{
    "mid": "5836069",
    "log_enabled": false,
    "auto_start": false,
    "update_interval": 30
}
"""

import requests
import threading
import json
import os
from mcdreforged.api.all import *

# 插件元数据
PLUGIN_METADATA = {
    'id': 'bilibili_follower',
    'version': '2.1',
    'name': 'Bilibili Follower Display',
    'description': '在游戏内通过假人显示B站粉丝数，支持定时自动更新与MID设置',
    'author': 'Assistant'
}

# 默认配置
config = {
    'mid': '5836069',           # 默认B站UP主MID
    'log_enabled': False,       # 是否启用详细日志
    'auto_start': False,         # 服务器启动时是否自动开启定时更新
    'update_interval': 60,      # 自动更新间隔（秒）
    'last_fans': None           # 缓存最后一次显示的粉丝数（已废弃，使用独立缓存文件）
}

# 数字朝向坐标（根据你的红石屏幕布局调整）
DIGIT_LOOK_AT = {
    0: "315 76 967", 1: "316 76 967", 2: "317 76 968",
    3: "317 76 969", 4: "317 76 970", 5: "316 76 971",
    6: "315 76 971", 7: "314 76 971", 8: "313 76 970",
    9: "313 76 969"
}
RESET_POS = "313.69 76 967"  # 复位位置
DELAY_BETWEEN_COMMANDS = 1.0  # 每个动作间隔（秒）

# 缓存文件名
CACHE_FILE = 'fan_cache.json'

# 全局变量
update_timer = None
server_inst = None  # 保存 MCDR server 实例

# ===== 工具函数 =====

def log_info(msg):
    """输出 INFO 日志"""
    if server_inst and config['log_enabled']:
        server_inst.logger.info(f"[Bilibili] {msg}")

def log_debug(msg):
    """输出 DEBUG 日志"""
    if server_inst and config['log_enabled']:
        server_inst.logger.debug(f"[Bilibili] {msg}")

def get_follower_count(mid):
    """获取B站粉丝数"""
    url = f"https://api.bilibili.com/x/web-interface/card?mid={mid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else {'code': -1}
    except Exception as e:
        log_info(f"请求失败: {e}")
        return {'code': -1}

def save_cache(fans_count):
    """保存粉丝数到缓存文件"""
    path = os.path.join(server_inst.get_data_folder(), CACHE_FILE)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'last_fans': int(fans_count)}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_info(f"缓存保存失败: {e}")

def load_cache():
    """从缓存文件读取粉丝数"""
    path = os.path.join(server_inst.get_data_folder(), CACHE_FILE)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('last_fans', None)
    except:
        return None

def display_number(server, number, only_changed=True):
    """
    显示数字到假人屏幕
    :param server: server 实例
    :param number: 要显示的数字
    :param only_changed: 是否仅更新变化的位数
    """
    digits = [int(d) for d in str(number)][::-1]  # 逆序：个位在前
    old_digits = [int(d) for d in str(load_cache())][::-1] if only_changed and load_cache() else []

    max_len = max(len(digits), len(old_digits)) if only_changed else len(digits)

    # 构建命令序列
    commands = [
        ("/player fan spawn at 315 76 969", "召唤假人"),
        (f"/player fan look at {RESET_POS}", "复位朝向"),
        ("/player fan use once", "触发复位")
    ]

    for i in range(max_len):
        cur = digits[i] if i < len(digits) else 0
        old = old_digits[i] if i < len(old_digits) else -1
        pos = DIGIT_LOOK_AT.get(cur, "315 76 967")

        if not only_changed or cur != old:
            commands.append((f"/player fan look at {pos}", f"显示第{i+1}位: {cur}"))
            commands.append(("/player fan use once", f"敲击第{i+1}位"))
        else:
            commands.append((f"/player fan look at {pos}", f"跳过第{i+1}位（未变）"))

    commands.append(("/player fan kill", "清理假人"))

    def run_cmd(index):
        if index >= len(commands):
            return
        cmd, desc = commands[index]
        server.execute(cmd)
        log_debug(f"{desc}: {cmd}")
        timer = threading.Timer(DELAY_BETWEEN_COMMANDS, run_cmd, [index + 1])
        timer.start()

    run_cmd(0)
    save_cache(number)

# ===== 定时任务控制 =====

def start_scheduled_update():
    """启动定时更新任务"""
    global update_timer
    if update_timer is not None:
        return  # 已在运行

    def task():
        global update_timer
        log_info("⏱️ 执行自动更新任务")
        # 使用 dispatch_server_command 确保触发 on_info 且 is_user=True
        server_inst.dispatch_server_command('!!fan update')
        update_timer = threading.Timer(config['update_interval'], task)
        update_timer.start()

    update_timer = threading.Timer(config['update_interval'], task)
    update_timer.start()
    server_inst.say(f"✅ 自动更新已启动，周期 {config['update_interval']} 秒")

def stop_scheduled_update():
    """停止定时更新"""
    global update_timer
    if update_timer is not None:
        update_timer.cancel()
        update_timer = None
        server_inst.say("🛑 自动更新已停止")

def get_task_status():
    """获取任务状态"""
    return "运行中" if update_timer is not None else "已停止"

# ===== 命令处理 =====

def on_info(server, info):
    global server_inst
    server_inst = server  # 保存实例

    # 忽略非用户输入
    if not info.is_user:
        return

    args = info.content.strip().split()
    if not args or args[0] != '!!fan':
        return

    # 日志调试
    log_debug(f"收到命令: {info.content}")

    # =============== 命令分发 ===============

    # 1. 查询粉丝数
    if len(args) == 1:
        data = get_follower_count(config['mid'])
        if data.get('code') == 0:
            fans = data['data']['card']['fans']
            name = data['data']['card']['name']
            server.say(f"📊 {name}: {fans:,} 粉丝")
        else:
            server.say("❌ 查询失败，请检查网络或MID")

    # 2. 设置 MID
    elif len(args) == 3 and args[1] == 'mid':
        new_mid = args[2]
        if not new_mid.isdigit() or len(new_mid) < 3 or len(new_mid) > 10:
            server.say("❌ 无效的 B站 MID，请输入 3~10 位数字")
            return

        old_mid = config['mid']
        if old_mid == new_mid:
            server.say(f"ℹ 当前已监控 MID: {old_mid}，无需更改")
            return

        config['mid'] = new_mid
        server.save_config_simple(config, 'bfanconfig.json')
        server.say(f"✅ 成功将监控的 UP 主 MID 从 {old_mid} 修改为 {new_mid}")

        # 如果自动更新正在运行，自动重启
        if update_timer is not None:
            server.say("🔄 检测到自动更新运行中，正在重启任务...")
            stop_scheduled_update()
            start_scheduled_update()
        return

    # 3. 首次显示
    elif args == ['!!fan', 'display']:
        data = get_follower_count(config['mid'])
        if data.get('code') == 0:
            fans = data['data']['card']['fans']
            name = data['data']['card']['name']
            server.say(f"🎨 正在显示 {name} 的粉丝数...")
            display_number(server, fans, only_changed=False)
        else:
            server.say("❌ 显示失败，请检查MID或网络")

    # 4. 智能更新（仅变化位）
    elif args == ['!!fan', 'update']:
        old_fans = load_cache()
        if old_fans is None:
            server.say("⚠ 请先使用 !!fan display 初始化显示")
            return

        data = get_follower_count(config['mid'])
        if data.get('code') == 0:
            fans = data['data']['card']['fans']
            name = data['data']['card']['name']
            server.say(f"🔄 {name}: {old_fans:,} → {fans:,}")
            display_number(server, fans, only_changed=True)
        else:
            server.say("❌ 更新失败")

    # 5. 日志开关
    elif args == ['!!fan', 'log', 'toggle']:
        config['log_enabled'] = not config['log_enabled']
        server.save_config_simple(config, 'bfanconfig.json')
        status = '开启' if config['log_enabled'] else '关闭'
        server.say(f"🔧 日志输出已 {status}")

    # 6. 定时任务控制
    elif args == ['!!fan', 'interval']:
        if get_task_status() == "运行中":
            stop_scheduled_update()
        else:
            start_scheduled_update()

    elif len(args) == 3 and args[1] == 'interval':
        cmd = args[2]
        if cmd == 'status':
            server.say(f"🔄 自动更新状态: {get_task_status()}")
        elif cmd == 'start':
            if get_task_status() == "运行中":
                server.say("ℹ 自动更新已在运行中")
            else:
                start_scheduled_update()
        elif cmd == 'stop':
            if get_task_status() == "已停止":
                server.say("ℹ 自动更新已停止")
            else:
                stop_scheduled_update()
        elif cmd.isdigit():
            interval = int(cmd)
            if interval < 5:
                server.say("❌ 间隔不能少于5秒")
                return
            config['update_interval'] = interval
            server.save_config_simple(config, 'bfanconfig.json')
            server.say(f"⏱️ 更新间隔已设置为 {interval} 秒")
            # 重启任务
            if update_timer is not None:
                stop_scheduled_update()
                start_scheduled_update()
        else:
            server.say("❌ 用法: !!fan interval <5~3600> | start | stop | status")

    # 7. 显示帮助
    elif args == ['!!fan', 'help']:
        server.reply(info, '''
§7====== §6Bilibili 粉丝显示 §7======
§a!!fan §f- 查询粉丝数
§a!!fan mid <mid> §f- 修改UP主MID
§a!!fan display §f- 首次显示
§a!!fan update §f- 智能更新
§a!!fan interval §f- 启/停自动更新
§a!!fan interval status §f- 查看状态
§a!!fan interval 30 §f- 设置间隔30秒
§a!!fan log toggle §f- 切换日志
§7========================§r
        '''.strip())

# ===== 插件生命周期 =====

def on_load(server, old_module):
    global server_inst
    server_inst = server

    # 创建数据目录
    data_folder = server.get_data_folder()
    os.makedirs(data_folder, exist_ok=True)

    # 加载配置文件
    config_path = os.path.join(data_folder, 'bfanconfig.json')
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            server.logger.warning(f"[Bilibili] 配置文件加载失败，使用默认值: {e}")

    # 保存配置（确保完整）
    server.save_config_simple(config, 'bfanconfig.json')
    server.logger.info(f"[Bilibili] 插件加载完成，MID={config['mid']}, 自动启动={config['auto_start']}")

    # 注册帮助
    server.register_help_message('!!fan', 'B站粉丝数显示')
    server.register_help_message('!!fan help', '查看所有命令')

    # 自动启动定时任务
    if config['auto_start']:
        start_scheduled_update()

def on_unload(server):
    """插件卸载时停止任务"""
    stop_scheduled_update()
    server.logger.info("[Bilibili] 插件已卸载")