import schedule
import time
import threading
from datetime import datetime, timedelta
import sys

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.tasks = []
        self.last_execution = {}
    
    def add_daily_task(self, time_str, task_func, task_name="定时任务"):
        """添加每日定时任务
        
        Args:
            time_str: 时间格式 "HH:MM" 如 "05:00" 
            task_func: 要执行的函数
            task_name: 任务名称
        """
        job = schedule.every().day.at(time_str).do(self._execute_task, task_func, task_name)
        job.tag = task_name
        self.tasks.append({
            'type': 'daily',
            'time': time_str,
            'name': task_name,
            'job': job
        })
        # logger.info(f"已添加每日任务: {task_name} - 每天 {time_str} 执行")
    
    def add_weekly_task(self, day, time_str, task_func, task_name="每周任务"):
        """添加每周定时任务
        
        Args:
            day: 星期几 (monday, tuesday, wednesday, thursday, friday, saturday, sunday)
            time_str: 时间格式 "HH:MM"
            task_func: 要执行的函数
            task_name: 任务名称
        """
        day_func = getattr(schedule.every(), day.lower())
        job = day_func.at(time_str).do(self._execute_task, task_func, task_name)
        job.tag = task_name
        self.tasks.append({
            'type': 'weekly',
            'day': day,
            'time': time_str,
            'name': task_name,
            'job': job
        })
        # logger.info(f"已添加每周任务: {task_name} - 每{day} {time_str} 执行")
    
    def add_interval_task(self, minutes, task_func, task_name="间隔任务"):
        """添加间隔执行任务
        
        Args:
            minutes: 间隔分钟数
            task_func: 要执行的函数  
            task_name: 任务名称
        """
        job = schedule.every(minutes).minutes.do(self._execute_task, task_func, task_name)
        job.tag = task_name
        self.tasks.append({
            'type': 'interval',
            'minutes': minutes,
            'name': task_name,
            'job': job
        })
        # logger.info(f"已添加间隔任务: {task_name} - 每 {minutes} 分钟执行")
    
    def _execute_task(self, task_func, task_name):
        """执行任务的内部方法"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # logger.info(f"[{current_time}] 开始执行任务: {task_name}")
            
            # 记录执行时间
            self.last_execution[task_name] = current_time
            
            # 执行任务
            result = task_func()
            
            if result:
                # logger.info(f"[{current_time}] 任务完成: {task_name} - 成功")
                pass
            else:
                # logger.warning(f"[{current_time}] 任务完成: {task_name} - 失败")
                pass
                
        except Exception as e:
            # logger.error(f"[{current_time}] 任务执行错误: {task_name} - {e}")
            pass
    
    def remove_task(self, task_name):
        """移除指定任务"""
        for task in self.tasks[:]:  # 复制列表以安全删除
            if task['name'] == task_name:
                schedule.cancel_job(task['job'])
                self.tasks.remove(task)
                # logger.info(f"已移除任务: {task_name}")
                return True
        # logger.warning(f"未找到任务: {task_name}")
        return False
    
    def list_tasks(self):
        """列出所有任务"""
        if not self.tasks:
            # logger.info("当前没有已安排的任务")
            return
        
        # logger.info("当前已安排的任务:")
        # print("-" * 60)
        for i, task in enumerate(self.tasks, 1):
            if task['type'] == 'daily':
                schedule_info = f"每天 {task['time']}"
            elif task['type'] == 'weekly':
                schedule_info = f"每{task['day']} {task['time']}"
            elif task['type'] == 'interval':
                schedule_info = f"每 {task['minutes']} 分钟"
            else:
                schedule_info = "未知类型"
            
            last_run = self.last_execution.get(task['name'], "从未执行")
            # logger.info(f"{i}. {task['name']}")
            # logger.info(f"   调度: {schedule_info}")
            # logger.info(f"   上次执行: {last_run}")
            # print()
    
    def get_next_run_time(self):
        """获取下次执行时间"""
        if not schedule.jobs:
            return None
        
        next_job = schedule.next_run()
        if next_job:
            return next_job.strftime("%Y-%m-%d %H:%M:%S")
        return None
    
    def start(self):
        """启动调度器"""
        if self.running:
            # logger.warning("调度器已经在运行")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        next_run = self.get_next_run_time()
        if next_run:
            # logger.info(f"调度器已启动，下次执行时间: {next_run}")
            pass
        else:
            # logger.info("调度器已启动，但没有已安排的任务")
            pass
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        # logger.info("调度器已停止")
    
    def _run_scheduler(self):
        """调度器主循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

def demo_task():
    """演示任务函数"""
    print("执行演示任务...")
    time.sleep(2)  # 模拟任务执行
    return True

def test_scheduler():
    """测试调度器功能"""
    scheduler = TaskScheduler()
    
    print("=== 定时任务调度器测试 ===\n")
    
    # 添加测试任务
    current_time = datetime.now()
    
    # 1分钟后执行的任务
    test_time = (current_time + timedelta(minutes=1)).strftime("%H:%M")
    scheduler.add_daily_task(test_time, demo_task, "1分钟后测试")
    
    # 每30秒执行的间隔任务
    scheduler.add_interval_task(0.5, demo_task, "30秒间隔测试")
    
    # 显示任务列表
    scheduler.list_tasks()
    
    # 启动调度器
    scheduler.start()
    
    try:
        print("\n调度器运行中... 按 Ctrl+C 停止")
        while True:
            time.sleep(10)
            print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}, 下次执行: {scheduler.get_next_run_time()}")
    except KeyboardInterrupt:
        print("\n正在停止调度器...")
        scheduler.stop()
        print("测试结束")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            test_scheduler()
        else:
            print(f"未知命令: {command}")
    else:
        print("定时任务调度器")
        print("\n用法:")
        print("  python task_scheduler.py test    # 测试调度器功能")
        print("\n功能:")
        print("- 支持每日定时任务")
        print("- 支持每周定时任务") 
        print("- 支持间隔执行任务")
        print("- 多线程后台运行")
        print("- 任务执行状态跟踪")

if __name__ == "__main__":
    main()