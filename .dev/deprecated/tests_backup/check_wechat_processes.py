import psutil

def find_all_wechat_processes():
    """查找所有微信相关进程"""
    wechat_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'ppid']):
        try:
            name = proc.info['name'] or ''
            if name.lower() == 'weixin.exe':
                wechat_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return wechat_processes

def main():
    processes = find_all_wechat_processes()
    print(f"找到 {len(processes)} 个微信进程:")
    
    for proc in processes:
        try:
            print(f"PID: {proc.pid}, PPID: {proc.ppid()}, 路径: {proc.exe()}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"PID: {proc.pid}, 无法获取详细信息")

if __name__ == "__main__":
    main()