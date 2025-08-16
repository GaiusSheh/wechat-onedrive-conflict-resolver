import psutil

def list_all_processes():
    """列出所有进程，帮助找到微信的实际进程名"""
    print("正在搜索所有进程...")
    wechat_related = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            name = proc.info['name'] or ''
            exe = proc.info['exe'] or ''
            
            # 查找可能与微信相关的进程
            if any(keyword.lower() in name.lower() for keyword in ['wechat', 'weixin', 'tencent']) or \
               any(keyword.lower() in exe.lower() for keyword in ['wechat', 'weixin', 'tencent']):
                wechat_related.append({
                    'pid': proc.info['pid'],
                    'name': name,
                    'exe': exe
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if wechat_related:
        print("\n找到可能的微信相关进程:")
        for proc in wechat_related:
            print(f"PID: {proc['pid']}, 进程名: {proc['name']}, 路径: {proc['exe']}")
    else:
        print("\n没有找到微信相关进程")
    
    return wechat_related

if __name__ == "__main__":
    list_all_processes()