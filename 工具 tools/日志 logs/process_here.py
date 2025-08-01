import os
import re
import gzip
import shutil
from datetime import datetime, timedelta
from collections import defaultdict

# 配置参数
encoding = 'gb18030' # 编码填写utf-8、gb18030或gbk等，目前为gb18030
raw_dir = 'raw'
archived_dir = 'archived'
error_dir = 'error'
logs_dir = 'logs'
chat_dir = 'chat'
modified_chats_file = 'modified_chats.txt'
blacklist_logs_file = 'blacklist_logs.txt'
whitelist_logs_file = 'whitelist_logs_file.txt'
blacklist_chat_file = 'blacklist_chat.txt'
whitelist_chat_file = 'whitelist_chat.txt'

# 初始化目录结构
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(chat_dir, exist_ok=True)
os.makedirs(archived_dir, exist_ok=True)
os.makedirs(error_dir, exist_ok=True)

def safe_file_open(file_path, mode='r'):
    """安全打开文件（支持gzip和不同编码格式文件）"""
    try:
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rb') as f:
                f.read(1)
            return gzip.open(file_path, mode + 't', encoding=encoding, errors='replace')
        else:
            with open(file_path, 'rb') as f:
                f.read(1)
            return open(file_path, mode, encoding=encoding, errors='replace') 
    except Exception as e:
        raise ValueError(f"文件打开失败: {file_path} - {str(e)}")

def load_patterns(file_path):
    """加载并编译正则表达式"""
    patterns = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        patterns.append(re.compile(line))
                    except re.error as e:
                        print(f"无效正则表达式: {line} - {str(e)}")
    except FileNotFoundError:
        print(f"未找到文件: {file_path}")
    return patterns

# 初始化黑白名单
blacklist_logs = load_patterns(blacklist_logs_file)
whitelist_logs = load_patterns(whitelist_logs_file)
blacklist_chat = load_patterns(blacklist_chat_file)
whitelist_chat = load_patterns(whitelist_chat_file)

# 数据存储结构
month_entries_logs = defaultdict(list)
month_entries_chat = defaultdict(list)
modified_chats = []
file_stats = defaultdict(dict)
global_stats = {
    'total_files': 0,
    'processed_files': 0,
    'error_files': 0,
    'total_lines': 0,
    'valid_messages_logs': 0,
    'blacklisted_messages_logs': 0,
    'non_whitelisted_messages_logs': 0,
    'valid_messages_chat': 0,
    'blacklisted_messages_chat': 0,
    'non_whitelisted_messages_chat': 0,
    'duplicate_messages_logs': 0,
    'duplicate_messages_chat': 0,
    'modified_messages': 0
}

def process_line(line, current_date, prev_time, blacklist, whitelist):
    """处理单行日志的完整流程"""
    time_match = re.match(r'\[(\d{2}:\d{2}:\d{2})\].*?(\[CHAT\]|\[聊天\])', line)
    if not time_match:
        return None, current_date, prev_time, 'invalid_format'
    
    try:
        log_time = datetime.strptime(time_match.group(1), '%H:%M:%S').time()
    except ValueError:
        return None, current_date, prev_time, 'invalid_time_format'
    
    if prev_time and log_time < prev_time:
        current_date += timedelta(days=1)
    prev_time = log_time
    full_dt = datetime.combine(current_date, log_time)

    chat_content = re.sub(r'^.*?(\[CHAT\]|\[聊天\])', '', line.strip()).strip()
    cleaned_content = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', chat_content).strip()
    check_msg = f"[CHAT] {cleaned_content}"
    
    if not any(p.search(check_msg) for p in whitelist):
        return None, current_date, prev_time, 'non_whitelisted'
    
    if any(p.search(cleaned_content) for p in blacklist):
        return None, current_date, prev_time, 'blacklisted'

    final_content = re.sub(r'\s{2,}', ' ', cleaned_content)
    if final_content != cleaned_content:
        modified_chats.append(f"原始: {chat_content} → 修改后: {final_content}")
        global_stats['modified_messages'] += 1

    return (full_dt, final_content), current_date, prev_time, 'valid'

def process_file(file_path, initial_date):
    """处理单个日志文件"""
    stats = {
        'total_lines': 0,
        'valid_messages_logs': 0,
        'blacklisted_logs': 0,
        'non_whitelisted_logs': 0,
        'valid_messages_chat': 0,
        'blacklisted_chat': 0,
        'non_whitelisted_chat': 0,
        'errors': 0
    }
    
    current_date = initial_date
    prev_time = None
    
    try:
        with safe_file_open(file_path) as f:
            for line in f:
                stats['total_lines'] += 1
                
                # 处理 logs
                result_logs, current_date, prev_time, status_logs = process_line(
                    line.strip(), current_date, prev_time, blacklist_logs, whitelist_logs
                )
                if status_logs == 'valid':
                    stats['valid_messages_logs'] += 1
                    dt, msg = result_logs
                    month_key = dt.strftime('%Y-%m')
                    formatted_time = dt.strftime('%Y-%m-%d-%H-%M-%S')
                    month_entries_logs[month_key].append((dt, f'[{formatted_time}] {msg}\n'))
                elif status_logs == 'blacklisted':
                    stats['blacklisted_logs'] += 1
                elif status_logs == 'non_whitelisted':
                    stats['non_whitelisted_logs'] += 1
                elif status_logs in ['invalid_format', 'invalid_time_format']:
                    stats['errors'] += 1
                
                # 处理 chat
                result_chat, _, _, status_chat = process_line(
                    line.strip(), current_date, prev_time, blacklist_chat, whitelist_chat
                )
                if status_chat == 'valid':
                    stats['valid_messages_chat'] += 1
                    dt, msg = result_chat
                    month_key = dt.strftime('%Y-%m')
                    formatted_time = dt.strftime('%Y-%m-%d-%H-%M-%S')
                    month_entries_chat[month_key].append((dt, f'[{formatted_time}] {msg}\n'))
                elif status_chat == 'blacklisted':
                    stats['blacklisted_chat'] += 1
                elif status_chat == 'non_whitelisted':
                    stats['non_whitelisted_chat'] += 1
        
        file_stats[file_path] = stats
        global_stats['total_lines'] += stats['total_lines']
        global_stats['valid_messages_logs'] += stats['valid_messages_logs']
        global_stats['blacklisted_messages_logs'] += stats['blacklisted_logs']
        global_stats['non_whitelisted_messages_logs'] += stats['non_whitelisted_logs']
        global_stats['valid_messages_chat'] += stats['valid_messages_chat']
        global_stats['blacklisted_messages_chat'] += stats['blacklisted_chat']
        global_stats['non_whitelisted_messages_chat'] += stats['non_whitelisted_chat']
        
        print(f"\n处理完成: {os.path.basename(file_path)}")
        print(f"├─ 总行数: {stats['total_lines']}")
        print(f"├─ 有效消息 (logs): {stats['valid_messages_logs']}")
        print(f"├─ 黑名单过滤 (logs): {stats['blacklisted_logs']}")
        print(f"├─ 未匹配白名单 (logs): {stats['non_whitelisted_logs']}")
        print(f"├─ 有效消息 (chat): {stats['valid_messages_chat']}")
        print(f"├─ 黑名单过滤 (chat): {stats['blacklisted_chat']}")
        print(f"└─ 未匹配白名单 (chat): {stats['non_whitelisted_chat']}")
        
        return True
    except Exception as e:
        print(f"\n处理失败: {os.path.basename(file_path)}")
        print(f"└─ 错误原因: {str(e)}")
        global_stats['error_files'] += 1
        return False

def save_modified_chats():
    """保存修改后的聊天记录"""
    if modified_chats:
        with open(modified_chats_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(modified_chats) + '\n')

def merge_and_save_logs(entries, output_dir, duplicate_key):
    """合并并保存最终日志"""
    total_duplicates = 0
    for month, entries in entries.items():
        log_file = os.path.join(output_dir, f'{month}.txt')
        existing = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                existing = [(line.split(']')[0][1:], line) for line in f]
        
        new_entries = [(dt.strftime('%Y-%m-%d-%H-%M-%S'), line) for dt, line in entries]
        seen = set()
        unique_entries = []
        for ts, line in sorted(existing + new_entries, key=lambda x: x[0]):
            if line not in seen:
                seen.add(line)
                unique_entries.append(line)
            else:
                total_duplicates += 1
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.writelines(unique_entries)
    
    global_stats[duplicate_key] = total_duplicates

def print_final_report():
    """打印最终统计报告"""
    print("\n" + "="*40)
    print("处理完成！汇总统计：")
    print(f"├─ 总处理文件: {global_stats['total_files']}")
    print(f"├─ 成功处理: {global_stats['processed_files']}")
    print(f"├─ 失败文件: {global_stats['error_files']}")
    print(f"├─ 总处理行数: {global_stats['total_lines']}")
    print(f"├─ 有效消息 (logs): {global_stats['valid_messages_logs']}")
    print(f"├─ 黑名单过滤 (logs): {global_stats['blacklisted_messages_logs']}")
    print(f"├─ 未匹配白名单 (logs): {global_stats['non_whitelisted_messages_logs']}")
    print(f"├─ 重复消息 (logs): {global_stats['duplicate_messages_logs']}")
    print(f"├─ 有效消息 (chat): {global_stats['valid_messages_chat']}")
    print(f"├─ 黑名单过滤 (chat): {global_stats['blacklisted_messages_chat']}")
    print(f"├─ 未匹配白名单 (chat): {global_stats['non_whitelisted_messages_chat']}")
    print(f"├─ 重复消息 (chat): {global_stats['duplicate_messages_chat']}")
    print(f"└─ 修改记录数: {global_stats['modified_messages']}")
    print("="*40)

def main():
    """主函数，仅处理raw目录中的日志文件"""
    file_list = []
    
    # 遍历raw目录中的所有文件
    for file in os.listdir(raw_dir):
        file_path = os.path.join(raw_dir, file)
        if os.path.isfile(file_path) and (file.endswith('.log') or file.endswith('.gz')):
            file_list.append(file_path)
    
    global_stats['total_files'] = len(file_list)
    print(f"发现 {len(file_list)} 个日志文件")
    
    for file_path in file_list:
        print(f"\n开始处理: {os.path.basename(file_path)}")
        match = re.search(r'.*?(\d{4})[-_]?(\d{2})[-_]?(\d{2}).*', os.path.basename(file_path))
        
        if match:
            year, month, day = map(int, match.groups())
            initial_date = datetime(year, month, day).date()
        elif os.path.basename(file_path) == 'latest.log':
            try:
                ctime = os.path.getmtime(file_path)
                initial_date = datetime.fromtimestamp(ctime).date()
            except Exception as e:
                print(f"获取文件时间失败: {str(e)}")
                initial_date = datetime.today().date()
        else:
            print("⚠️ 无法识别日期，使用当天日期")
            initial_date = datetime.today().date()
        
        if process_file(file_path, initial_date):
            global_stats['processed_files'] += 1
            # 移动处理成功的文件到archived目录
            archived_path = os.path.join(archived_dir, os.path.basename(file_path))
            shutil.move(file_path, archived_path)
        else:
            # 移动处理失败的文件到error目录
            error_path = os.path.join(error_dir, os.path.basename(file_path))
            shutil.move(file_path, error_path)
    
    save_modified_chats()
    merge_and_save_logs(month_entries_logs, logs_dir, 'duplicate_messages_logs')
    merge_and_save_logs(month_entries_chat, chat_dir, 'duplicate_messages_chat')
    print_final_report()

if __name__ == '__main__':
    main()