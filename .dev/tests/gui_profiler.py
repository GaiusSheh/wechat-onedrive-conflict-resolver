#!/usr/bin/env python3
"""
GUI性能分析工具 - 遵循profiling原则
记录用户交互的响应时间，按层级组织性能数据

设计原则：
1. 非侵入式监控 - 不修改现有GUI代码
2. 分层记录 - 按组件、操作、时间维度组织数据
3. 响应时间追踪 - 从用户操作到界面响应完成
4. 保持GUI完整性 - 只观察，不修改
"""

import time
import threading
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import json
from pathlib import Path

@dataclass
class PerformanceEvent:
    """性能事件记录"""
    event_id: str
    event_type: str  # 'user_action', 'gui_update', 'system_response'
    component: str   # 组件名称
    action: str      # 具体操作
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    parent_event: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def finish(self, end_time: Optional[float] = None):
        """完成事件记录"""
        self.end_time = end_time or time.time()
        self.duration = self.end_time - self.start_time
        return self.duration

@dataclass
class InteractionSession:
    """用户交互会话"""
    session_id: str
    start_time: float
    events: List[PerformanceEvent] = field(default_factory=list)
    end_time: Optional[float] = None
    
    def add_event(self, event: PerformanceEvent):
        """添加事件"""
        self.events.append(event)
    
    def finish(self):
        """结束会话"""
        self.end_time = time.time()

class GUIProfiler:
    """GUI性能分析器"""
    
    def __init__(self, output_dir: str = "performance_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 性能数据存储
        self.current_session: Optional[InteractionSession] = None
        self.sessions: List[InteractionSession] = []
        self.active_events: Dict[str, PerformanceEvent] = {}
        
        # 统计数据
        self.component_stats = defaultdict(lambda: {
            'total_time': 0.0,
            'call_count': 0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf')
        })
        
        self.interaction_history = deque(maxlen=1000)
        
        # 分层数据组织
        self.hierarchy = {
            'GUI_Components': {
                'MainWindow': ['按钮点击', '窗口更新', '状态刷新'],
                'ConfigPanel': ['配置加载', '配置保存', '界面切换'],
                'SystemTray': ['托盘更新', '通知显示', '菜单操作'],
                'LogDisplay': ['日志添加', '滚动更新', '颜色渲染']
            },
            'System_Operations': {
                'ProcessControl': ['微信操作', 'OneDrive操作', '状态检查'],
                'FileOperations': ['配置读写', '日志写入', '图标加载'],
                'NetworkOperations': ['状态查询', '同步检测']
            },
            'Performance_Thresholds': {
                'Excellent': 50,   # 50ms以下
                'Good': 100,       # 100ms以下  
                'Acceptable': 200, # 200ms以下
                'Slow': 500,       # 500ms以下
                'Very_Slow': 1000  # 1000ms以下
            }
        }
        
        self._lock = threading.Lock()
    
    def start_session(self, session_name: str = None) -> str:
        """开始新的分析会话"""
        session_id = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self._lock:
            if self.current_session:
                self.current_session.finish()
                self.sessions.append(self.current_session)
            
            self.current_session = InteractionSession(
                session_id=session_id,
                start_time=time.time()
            )
        
        self._log_event("SESSION", f"开始分析会话: {session_id}")
        return session_id
    
    def track_user_interaction(self, component: str, action: str, 
                             metadata: Dict = None) -> str:
        """追踪用户交互开始"""
        event_id = f"{component}_{action}_{int(time.time()*1000)}"
        
        event = PerformanceEvent(
            event_id=event_id,
            event_type='user_action',
            component=component,
            action=action,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self.active_events[event_id] = event
            if self.current_session:
                self.current_session.add_event(event)
        
        self._log_event("USER_ACTION", f"{component}.{action} 开始")
        return event_id
    
    def finish_interaction(self, event_id: str, success: bool = True, 
                          result_metadata: Dict = None):
        """完成用户交互追踪"""
        with self._lock:
            if event_id in self.active_events:
                event = self.active_events.pop(event_id)
                duration = event.finish()
                
                # 更新元数据
                if result_metadata:
                    event.metadata.update(result_metadata)
                event.metadata['success'] = success
                
                # 更新统计
                self._update_component_stats(event.component, duration)
                
                # 记录交互历史
                self.interaction_history.append({
                    'timestamp': datetime.fromtimestamp(event.start_time),
                    'component': event.component,
                    'action': event.action,
                    'duration_ms': duration * 1000,
                    'success': success
                })
                
                # 性能等级评估
                perf_level = self._get_performance_level(duration * 1000)
                
                self._log_event("INTERACTION_COMPLETE", 
                               f"{event.component}.{event.action} 完成: {duration*1000:.1f}ms ({perf_level})")
                
                return duration
        
        return None
    
    def track_gui_update(self, component: str, operation: str, 
                        start_time: float = None) -> str:
        """追踪GUI更新操作"""
        event_id = f"gui_{component}_{operation}_{int(time.time()*1000)}"
        
        event = PerformanceEvent(
            event_id=event_id,
            event_type='gui_update',
            component=component,
            action=operation,
            start_time=start_time or time.time()
        )
        
        with self._lock:
            self.active_events[event_id] = event
        
        return event_id
    
    def finish_gui_update(self, event_id: str):
        """完成GUI更新追踪"""
        with self._lock:
            if event_id in self.active_events:
                event = self.active_events.pop(event_id)
                duration = event.finish()
                self._update_component_stats(f"GUI_{event.component}", duration)
                return duration
        return None
    
    def _update_component_stats(self, component: str, duration: float):
        """更新组件统计数据"""
        stats = self.component_stats[component]
        stats['total_time'] += duration
        stats['call_count'] += 1
        stats['avg_time'] = stats['total_time'] / stats['call_count']
        stats['max_time'] = max(stats['max_time'], duration)
        stats['min_time'] = min(stats['min_time'], duration)
    
    def _get_performance_level(self, duration_ms: float) -> str:
        """获取性能等级"""
        thresholds = self.hierarchy['Performance_Thresholds']
        
        if duration_ms <= thresholds['Excellent']:
            return 'Excellent'
        elif duration_ms <= thresholds['Good']:
            return 'Good'
        elif duration_ms <= thresholds['Acceptable']:
            return 'Acceptable'
        elif duration_ms <= thresholds['Slow']:
            return 'Slow'
        else:
            return 'Very_Slow'
    
    def _log_event(self, event_type: str, message: str):
        """记录分析事件"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] [{event_type}] {message}")
    
    def generate_performance_report(self) -> Dict:
        """生成性能分析报告"""
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'session_count': len(self.sessions) + (1 if self.current_session else 0),
            'component_performance': dict(self.component_stats),
            'interaction_summary': self._get_interaction_summary(),
            'performance_distribution': self._get_performance_distribution(),
            'bottleneck_analysis': self._identify_bottlenecks(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _get_interaction_summary(self) -> Dict:
        """获取交互摘要"""
        if not self.interaction_history:
            return {}
        
        total_interactions = len(self.interaction_history)
        avg_response_time = sum(item['duration_ms'] for item in self.interaction_history) / total_interactions
        success_rate = sum(1 for item in self.interaction_history if item['success']) / total_interactions
        
        # 按组件分组统计
        component_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'failures': 0})
        for item in self.interaction_history:
            comp_stat = component_stats[item['component']]
            comp_stat['count'] += 1
            comp_stat['total_time'] += item['duration_ms']
            if not item['success']:
                comp_stat['failures'] += 1
        
        return {
            'total_interactions': total_interactions,
            'average_response_time_ms': avg_response_time,
            'success_rate': success_rate,
            'component_breakdown': dict(component_stats)
        }
    
    def _get_performance_distribution(self) -> Dict:
        """获取性能分布"""
        distribution = defaultdict(int)
        
        for item in self.interaction_history:
            level = self._get_performance_level(item['duration_ms'])
            distribution[level] += 1
        
        return dict(distribution)
    
    def _identify_bottlenecks(self) -> List[Dict]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        # 找出平均响应时间超过阈值的组件
        for component, stats in self.component_stats.items():
            avg_time_ms = stats['avg_time'] * 1000
            if avg_time_ms > self.hierarchy['Performance_Thresholds']['Acceptable']:
                bottlenecks.append({
                    'component': component,
                    'avg_response_time_ms': avg_time_ms,
                    'max_response_time_ms': stats['max_time'] * 1000,
                    'call_count': stats['call_count'],
                    'severity': self._get_performance_level(avg_time_ms)
                })
        
        # 按平均响应时间排序
        bottlenecks.sort(key=lambda x: x['avg_response_time_ms'], reverse=True)
        
        return bottlenecks
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        bottlenecks = self._identify_bottlenecks()
        
        if bottlenecks:
            recommendations.append("发现性能瓶颈，建议优先处理以下组件：")
            for bottleneck in bottlenecks[:3]:  # 显示前3个最严重的
                recommendations.append(f"  - {bottleneck['component']}: "
                                     f"{bottleneck['avg_response_time_ms']:.1f}ms "
                                     f"({bottleneck['severity']})")
        
        # 基于性能分布给出建议
        perf_dist = self._get_performance_distribution()
        total = sum(perf_dist.values())
        
        if total > 0:
            slow_ratio = (perf_dist.get('Slow', 0) + perf_dist.get('Very_Slow', 0)) / total
            if slow_ratio > 0.1:
                recommendations.append(f"有{slow_ratio*100:.1f}%的操作响应较慢，建议进行性能优化")
        
        return recommendations
    
    def save_report(self, filename: str = None):
        """保存性能报告"""
        report = self.generate_performance_report()
        filename = filename or f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self._log_event("REPORT", f"性能报告已保存: {filepath}")
        return filepath

# 全局profiler实例
gui_profiler = GUIProfiler()

# 便捷装饰器
def profile_user_interaction(component: str, action: str):
    """装饰器：自动追踪用户交互性能"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            event_id = gui_profiler.track_user_interaction(component, action)
            try:
                result = func(*args, **kwargs)
                gui_profiler.finish_interaction(event_id, success=True)
                return result
            except Exception as e:
                gui_profiler.finish_interaction(event_id, success=False, 
                                               result_metadata={'error': str(e)})
                raise
        return wrapper
    return decorator

def profile_gui_update(component: str, operation: str):
    """装饰器：自动追踪GUI更新性能"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            event_id = gui_profiler.track_gui_update(component, operation)
            try:
                result = func(*args, **kwargs)
                gui_profiler.finish_gui_update(event_id)
                return result
            except Exception as e:
                gui_profiler.finish_gui_update(event_id)
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # 测试profiler
    profiler = GUIProfiler()
    
    print("=== GUI性能分析工具测试 ===")
    
    # 模拟用户交互
    profiler.start_session("test_session")
    
    # 模拟按钮点击
    event1 = profiler.track_user_interaction("MainWindow", "同步按钮点击")
    time.sleep(0.15)  # 模拟150ms响应
    profiler.finish_interaction(event1, success=True)
    
    # 模拟配置加载
    event2 = profiler.track_user_interaction("ConfigPanel", "配置加载")
    time.sleep(0.05)  # 模拟50ms响应
    profiler.finish_interaction(event2, success=True)
    
    # 模拟慢操作
    event3 = profiler.track_user_interaction("SystemTray", "状态更新")
    time.sleep(0.3)   # 模拟300ms响应
    profiler.finish_interaction(event3, success=True)
    
    # 生成报告
    report_path = profiler.save_report()
    print(f"\n性能报告已生成: {report_path}")
    
    # 显示简要报告
    report = profiler.generate_performance_report()
    print(f"\n=== 性能摘要 ===")
    print(f"总交互次数: {report['interaction_summary']['total_interactions']}")
    print(f"平均响应时间: {report['interaction_summary']['average_response_time_ms']:.1f}ms")
    print(f"成功率: {report['interaction_summary']['success_rate']*100:.1f}%")
    
    if report['bottleneck_analysis']:
        print(f"\n=== 性能瓶颈 ===")
        for bottleneck in report['bottleneck_analysis']:
            print(f"- {bottleneck['component']}: {bottleneck['avg_response_time_ms']:.1f}ms ({bottleneck['severity']})")
    
    print(f"\n=== 优化建议 ===")
    for rec in report['recommendations']:
        print(f"- {rec}")