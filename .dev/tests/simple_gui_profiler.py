#!/usr/bin/env python3
"""
简化的GUI性能分析器
完全非侵入性设计，遵循项目规则：
- 不修改现有GUI代码
- 不使用emoji避免命令行问题
- 专注于记录用户交互响应时间
- 按层级组织性能数据
"""

import time
import threading
from datetime import datetime
from collections import deque, defaultdict
from pathlib import Path
import json

class SimpleGUIProfiler:
    """简化的GUI性能分析器"""
    
    def __init__(self):
        self.active = False
        self.start_time = None
        
        # 存储交互记录
        self.interactions = deque(maxlen=1000)
        
        # 性能统计
        self.component_stats = defaultdict(lambda: {
            'total_time': 0.0,
            'count': 0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'slow_count': 0  # 超过200ms的操作数
        })
        
        self.session_start = time.time()
    
    def start_profiling(self):
        """开始性能分析"""
        self.active = True
        self.session_start = time.time()
        print(f"[PROFILER] 性能分析已启动 - {datetime.now().strftime('%H:%M:%S')}")
    
    def stop_profiling(self):
        """停止性能分析"""
        self.active = False
        print(f"[PROFILER] 性能分析已停止 - {datetime.now().strftime('%H:%M:%S')}")
        self.save_results()
    
    def record_interaction(self, component, action, start_time=None):
        """记录交互开始时间"""
        if not self.active:
            return None
        
        interaction_id = f"{component}_{action}_{int(time.time() * 1000)}"
        record = {
            'id': interaction_id,
            'component': component,
            'action': action,
            'start_time': start_time or time.time(),
            'end_time': None,
            'duration_ms': None
        }
        
        return record
    
    def finish_interaction(self, record, end_time=None):
        """完成交互记录"""
        if not self.active or not record:
            return
        
        record['end_time'] = end_time or time.time()
        record['duration_ms'] = (record['end_time'] - record['start_time']) * 1000
        
        # 添加到记录中
        self.interactions.append(record)
        
        # 更新统计
        component = record['component']
        duration_ms = record['duration_ms']
        
        stats = self.component_stats[component]
        stats['count'] += 1
        stats['total_time'] += duration_ms
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], duration_ms)
        
        if duration_ms > 200:  # 超过200ms认为是慢操作
            stats['slow_count'] += 1
        
        # 实时反馈慢操作
        if duration_ms > 300:
            print(f"[PROFILER] 慢操作检测: {component}.{record['action']} - {duration_ms:.1f}ms")
    
    def get_summary(self):
        """获取性能摘要"""
        if not self.interactions:
            return "暂无性能数据"
        
        total_interactions = len(self.interactions)
        total_time = sum(i['duration_ms'] for i in self.interactions)
        avg_time = total_time / total_interactions
        
        slow_interactions = [i for i in self.interactions if i['duration_ms'] > 200]
        slow_count = len(slow_interactions)
        slow_ratio = slow_count / total_interactions * 100
        
        summary = f"""
=== GUI性能分析摘要 ===
分析时长: {(time.time() - self.session_start):.1f}秒
总交互次数: {total_interactions}
平均响应时间: {avg_time:.1f}ms
慢操作数量: {slow_count} ({slow_ratio:.1f}%)

=== 组件性能排行 ==="""
        
        # 按平均时间排序显示top5
        sorted_components = sorted(
            self.component_stats.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )
        
        for i, (component, stats) in enumerate(sorted_components[:5], 1):
            summary += f"""
{i}. {component}:
   平均: {stats['avg_time']:.1f}ms
   最大: {stats['max_time']:.1f}ms
   慢操作: {stats['slow_count']}/{stats['count']}"""
        
        return summary
    
    def save_results(self):
        """保存结果到文件"""
        output_dir = Path(".dev") / "performance_data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gui_performance_{timestamp}.json"
        
        data = {
            'session_info': {
                'start_time': self.session_start,
                'end_time': time.time(),
                'total_interactions': len(self.interactions)
            },
            'interactions': list(self.interactions),
            'component_stats': dict(self.component_stats),
            'summary': self.get_summary()
        }
        
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"[PROFILER] 性能数据已保存: {output_path}")
        return output_path

# 全局实例
profiler = SimpleGUIProfiler()

def profile_button_click(component, action):
    """简单的按钮点击性能分析装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 记录开始
            record = profiler.record_interaction(component, action)
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录结束
                profiler.finish_interaction(record)
                
                return result
            except Exception as e:
                # 即使出错也要记录
                profiler.finish_interaction(record)
                raise
        
        return wrapper
    return decorator

def manual_timing(component, action):
    """手动计时上下文管理器"""
    class TimingContext:
        def __init__(self, component, action):
            self.record = profiler.record_interaction(component, action)
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            profiler.finish_interaction(self.record)
    
    return TimingContext(component, action)

# 使用示例函数
def demo_usage():
    """演示如何使用性能分析器"""
    print("=== GUI性能分析器使用演示 ===")
    
    # 1. 启动分析
    profiler.start_profiling()
    
    # 2. 模拟一些GUI操作
    
    # 方法1: 使用装饰器
    @profile_button_click("MainWindow", "同步按钮")
    def simulate_sync_click():
        time.sleep(0.15)  # 模拟150ms操作
        return "同步完成"
    
    # 方法2: 手动计时
    def simulate_status_update():
        with manual_timing("StatusPanel", "状态刷新"):
            time.sleep(0.05)  # 模拟50ms操作
    
    # 方法3: 记录慢操作
    def simulate_slow_operation():
        with manual_timing("ConfigPanel", "配置加载"):
            time.sleep(0.35)  # 模拟350ms慢操作
    
    # 执行测试
    simulate_sync_click()
    simulate_status_update()
    simulate_slow_operation()
    
    # 再执行几次以获得统计数据
    simulate_sync_click()
    simulate_status_update()
    
    # 3. 显示摘要
    print(profiler.get_summary())
    
    # 4. 停止分析
    profiler.stop_profiling()

if __name__ == "__main__":
    demo_usage()