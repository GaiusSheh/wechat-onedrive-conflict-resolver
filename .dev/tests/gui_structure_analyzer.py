#!/usr/bin/env python3
"""
GUI结构分析工具
遵循"只注释，不修改"原则，分析现有GUI结构中的潜在性能问题

分析维度：
1. 代码结构分析 - 找出可能的性能瓶颈点
2. GUI组件层次分析 - 理解界面更新路径
3. 事件处理流程分析 - 追踪用户操作响应链
4. 线程和并发分析 - 识别阻塞操作
5. 资源使用分析 - 内存、CPU密集操作

输出：详细的结构分析报告和性能优化建议（仅注释形式）
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json

@dataclass
class CodeElement:
    """代码元素"""
    name: str
    element_type: str  # 'class', 'method', 'function'
    file_path: str
    line_number: int
    complexity_score: int = 0
    performance_indicators: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
@dataclass 
class PerformanceConcern:
    """性能关注点"""
    concern_type: str  # 'blocking_operation', 'frequent_updates', 'memory_leak'
    severity: str      # 'low', 'medium', 'high', 'critical'
    location: str      # 文件:行号
    description: str
    recommendation: str
    code_snippet: str = ""

class GUIStructureAnalyzer:
    """GUI结构分析器"""
    
    def __init__(self, gui_dir: str = "gui"):
        self.gui_dir = Path(gui_dir)
        self.analysis_results = {
            'code_elements': [],
            'performance_concerns': [],
            'component_hierarchy': {},
            'event_flow_analysis': {},
            'threading_analysis': {},
            'resource_usage_patterns': {}
        }
        
        # 性能关注的关键词
        self.performance_keywords = {
            'blocking_operations': [
                'time.sleep', 'subprocess.run', 'requests.get', 'requests.post',
                '.wait()', 'join()', 'acquire()', 'input()', 'print('
            ],
            'frequent_updates': [
                '.after(', 'while True', 'for.*in.*range', 'update_idletasks',
                '.config(', '.configure(', 'self.root.after'
            ],
            'memory_concerns': [
                'global ', '[]', 'defaultdict', 'deque', 'append(', 'extend('
            ],
            'gui_intensive': [
                '.grid(', '.pack(', '.place(', 'create_widgets', 'ttk.',
                'tk.', '.destroy()', '.winfo_', 'messagebox'
            ]
        }
        
        # GUI组件模式
        self.gui_patterns = {
            'main_window_class': r'class\s+MainWindow',
            'widget_creation': r'(ttk\.|tk\.)\w+\(',
            'event_binding': r'\.bind\(',
            'callback_methods': r'def\s+(on_\w+|handle_\w+)',
            'update_methods': r'def\s+(update_\w+|refresh_\w+)',
            'threading_usage': r'threading\.(Thread|Timer)',
            'after_scheduling': r'\.after\(',
        }
    
    def analyze_gui_structure(self) -> Dict:
        """分析GUI结构"""
        print("🔍 开始GUI结构分析...")
        
        # 1. 分析所有Python文件
        for py_file in self.gui_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
            self._analyze_file(py_file)
        
        # 2. 生成组件层次结构
        self._build_component_hierarchy()
        
        # 3. 分析事件流
        self._analyze_event_flows()
        
        # 4. 分析线程使用
        self._analyze_threading_patterns()
        
        # 5. 识别性能关注点
        self._identify_performance_concerns()
        
        print("✅ GUI结构分析完成")
        return self.analysis_results
    
    def _analyze_file(self, file_path: Path):
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST分析
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path)
            except SyntaxError:
                pass
            
            # 正则表达式分析
            self._analyze_patterns(content, file_path)
            
        except Exception as e:
            print(f"⚠️  分析文件失败 {file_path}: {e}")
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path):
        """使用AST分析代码结构"""
        class_analyzer = ASTClassAnalyzer(str(file_path))
        class_analyzer.visit(tree)
        
        self.analysis_results['code_elements'].extend(class_analyzer.elements)
    
    def _analyze_patterns(self, content: str, file_path: Path):
        """分析代码模式"""
        lines = content.split('\n')
        
        for line_no, line in enumerate(lines, 1):
            # 检查性能关键词
            for category, keywords in self.performance_keywords.items():
                for keyword in keywords:
                    if keyword in line and not line.strip().startswith('#'):
                        concern = PerformanceConcern(
                            concern_type=category,
                            severity='medium',  # 默认中等严重性
                            location=f"{file_path.name}:{line_no}",
                            description=f"发现{category}相关代码: {keyword}",
                            recommendation=self._get_recommendation(category, keyword),
                            code_snippet=line.strip()
                        )
                        
                        # 根据上下文调整严重性
                        concern.severity = self._assess_severity(line, category)
                        
                        self.analysis_results['performance_concerns'].append(concern)
    
    def _get_recommendation(self, category: str, keyword: str) -> str:
        """获取优化建议"""
        recommendations = {
            'blocking_operations': {
                'time.sleep': "避免在GUI线程中使用time.sleep，考虑使用.after()调度",
                'subprocess.run': "将subprocess操作移至后台线程，避免阻塞GUI",
                'requests.get': "使用异步请求或后台线程处理网络操作",
                'print(': "在生产环境中避免频繁的print输出，影响性能"
            },
            'frequent_updates': {
                '.after(': "检查.after()调用频率，避免过于频繁的更新",
                'while True': "GUI线程中的无限循环可能导致界面冻结",
                'update_idletasks': "频繁调用update_idletasks可能影响性能"
            },
            'memory_concerns': {
                'global ': "过多全局变量可能导致内存泄漏",
                'append(': "检查列表是否有清理机制，避免无限增长"
            },
            'gui_intensive': {
                '.grid(': "批量组件操作时考虑使用update_idletasks优化",
                'messagebox': "频繁的消息框可能影响用户体验"
            }
        }
        
        return recommendations.get(category, {}).get(keyword, f"审查{keyword}的使用模式")
    
    def _assess_severity(self, line: str, category: str) -> str:
        """评估严重性"""
        # 在循环中的操作更严重
        if any(pattern in line for pattern in ['for ', 'while ', 'range(']):
            if category == 'blocking_operations':
                return 'high'
            else:
                return 'medium'
        
        # 在.after()中的频繁操作
        if '.after(' in line and any(ms in line for ms in ['1)', '10)', '50)']):
            return 'high'
        
        # 默认严重性
        severity_map = {
            'blocking_operations': 'medium',
            'frequent_updates': 'low',
            'memory_concerns': 'low',
            'gui_intensive': 'low'
        }
        
        return severity_map.get(category, 'low')
    
    def _build_component_hierarchy(self):
        """构建组件层次结构"""
        hierarchy = {}
        
        # 从代码元素中提取组件关系
        classes = [elem for elem in self.analysis_results['code_elements'] 
                  if elem.element_type == 'class']
        
        for cls in classes:
            component_info = {
                'file': cls.file_path,
                'methods': [elem.name for elem in self.analysis_results['code_elements']
                           if elem.element_type == 'method' and cls.file_path in elem.file_path],
                'complexity': cls.complexity_score,
                'performance_indicators': cls.performance_indicators
            }
            hierarchy[cls.name] = component_info
        
        self.analysis_results['component_hierarchy'] = hierarchy
    
    def _analyze_event_flows(self):
        """分析事件流"""
        event_flows = {}
        
        # 查找事件处理方法
        event_methods = []
        for elem in self.analysis_results['code_elements']:
            if elem.element_type == 'method':
                if (elem.name.startswith('on_') or 
                    elem.name.startswith('handle_') or
                    elem.name.endswith('_callback')):
                    event_methods.append(elem)
        
        # 分析每个事件的复杂度
        for method in event_methods:
            flow_info = {
                'location': f"{method.file_path}:{method.line_number}",
                'complexity': method.complexity_score,
                'dependencies': method.dependencies,
                'performance_risk': 'low'
            }
            
            # 根据复杂度和依赖评估风险
            if method.complexity_score > 10:
                flow_info['performance_risk'] = 'high'
            elif method.complexity_score > 5:
                flow_info['performance_risk'] = 'medium'
            
            event_flows[method.name] = flow_info
        
        self.analysis_results['event_flow_analysis'] = event_flows
    
    def _analyze_threading_patterns(self):
        """分析线程使用模式"""
        threading_analysis = {
            'thread_creation_patterns': [],
            'potential_race_conditions': [],
            'gui_thread_violations': []
        }
        
        # 查找线程相关的性能问题
        for concern in self.analysis_results['performance_concerns']:
            if 'threading' in concern.code_snippet.lower():
                threading_analysis['thread_creation_patterns'].append({
                    'location': concern.location,
                    'pattern': concern.code_snippet,
                    'recommendation': concern.recommendation
                })
        
        self.analysis_results['threading_analysis'] = threading_analysis
    
    def _identify_performance_concerns(self):
        """识别和分类性能关注点"""
        # 按严重性排序
        concerns_by_severity = defaultdict(list)
        for concern in self.analysis_results['performance_concerns']:
            concerns_by_severity[concern.severity].append(concern)
        
        # 添加高级分析
        self._add_advanced_concerns(concerns_by_severity)
        
        # 重新组织关注点
        sorted_concerns = []
        for severity in ['critical', 'high', 'medium', 'low']:
            sorted_concerns.extend(concerns_by_severity[severity])
        
        self.analysis_results['performance_concerns'] = sorted_concerns
    
    def _add_advanced_concerns(self, concerns_by_severity):
        """添加高级性能关注点"""
        # 如果发现大量blocking操作，标记为critical
        blocking_count = len([c for c in self.analysis_results['performance_concerns']
                            if c.concern_type == 'blocking_operations'])
        
        if blocking_count > 10:
            critical_concern = PerformanceConcern(
                concern_type='architecture',
                severity='critical',
                location='multiple_files',
                description=f"发现{blocking_count}个潜在的阻塞操作，可能严重影响GUI响应性",
                recommendation="建议重构架构，将阻塞操作移至后台线程"
            )
            concerns_by_severity['critical'].append(critical_concern)
    
    def generate_analysis_report(self) -> str:
        """生成分析报告"""
        results = self.analysis_results
        
        report = f"""
# GUI结构性能分析报告
生成时间: {os.popen('date /t & time /t').read().strip()}

## 📊 总体概览
- 分析的代码元素: {len(results['code_elements'])}
- 发现的性能关注点: {len(results['performance_concerns'])}  
- GUI组件类: {len(results['component_hierarchy'])}
- 事件处理方法: {len(results['event_flow_analysis'])}

## 🚨 严重性能关注点

"""
        
        # 按严重性分组显示关注点
        severity_order = ['critical', 'high', 'medium', 'low']
        concerns_by_severity = defaultdict(list)
        
        for concern in results['performance_concerns']:
            concerns_by_severity[concern.severity].append(concern)
        
        for severity in severity_order:
            if concerns_by_severity[severity]:
                report += f"### {severity.upper()} 严重性 ({len(concerns_by_severity[severity])}个)\n\n"
                
                for concern in concerns_by_severity[severity][:5]:  # 只显示前5个
                    report += f"""
**{concern.concern_type}** - `{concern.location}`
- 描述: {concern.description}
- 代码: `{concern.code_snippet[:60]}{'...' if len(concern.code_snippet) > 60 else ''}`
- 建议: {concern.recommendation}

"""
        
        # 组件层次分析
        report += """
## 🏗️ 组件结构分析

"""
        
        for comp_name, comp_info in results['component_hierarchy'].items():
            complexity_level = "高" if comp_info['complexity'] > 10 else "中" if comp_info['complexity'] > 5 else "低"
            report += f"""
### {comp_name}
- 文件: `{comp_info['file']}`
- 方法数量: {len(comp_info['methods'])}
- 复杂度: {comp_info['complexity']} ({complexity_level})
- 性能指标: {', '.join(comp_info['performance_indicators']) if comp_info['performance_indicators'] else '无'}

"""
        
        # 事件流分析
        report += """
## ⚡ 事件响应分析

"""
        
        high_risk_events = {name: info for name, info in results['event_flow_analysis'].items() 
                           if info['performance_risk'] in ['high', 'medium']}
        
        if high_risk_events:
            for event_name, event_info in high_risk_events.items():
                report += f"""
### {event_name}
- 位置: `{event_info['location']}`
- 复杂度: {event_info['complexity']}
- 性能风险: **{event_info['performance_risk'].upper()}**
- 依赖: {', '.join(event_info['dependencies'][:3]) if event_info['dependencies'] else '无'}

"""
        else:
            report += "✅ 未发现高风险的事件处理方法\n\n"
        
        # 优化建议
        report += """
## 💡 性能优化建议

基于分析结果，建议按以下优先级进行优化：

### 立即处理 (Critical & High)
"""
        
        critical_high = [c for c in results['performance_concerns'] 
                        if c.severity in ['critical', 'high']]
        
        if critical_high:
            for i, concern in enumerate(critical_high[:5], 1):
                report += f"{i}. **{concern.location}**: {concern.recommendation}\n"
        else:
            report += "✅ 无严重性能问题需要立即处理\n"
        
        report += """
### 中期优化 (Medium)
- 审查所有medium级别的性能关注点
- 考虑重构复杂度高的组件
- 优化频繁更新的GUI操作

### 长期维护 (Low)  
- 建立持续的性能监控
- 定期review代码中的性能反模式
- 建立性能测试基准

## 📏 性能监控建议

1. **集成GUI性能分析器**: 使用tools/gui_profiler.py监控实际运行性能
2. **设置性能基准**: 建立响应时间的可接受阈值
3. **定期分析**: 每次重大修改后运行此结构分析
4. **用户体验测试**: 定期测试真实使用场景下的响应性

---
*此报告基于静态代码分析生成，实际性能还需要运行时profiling验证*
"""
        
        return report
    
    def save_analysis_report(self, filename: str = None):
        """保存分析报告"""
        report_content = self.generate_analysis_report()
        
        if filename is None:
            filename = f"gui_structure_analysis_{os.popen('date /t').read().strip().replace('/', '')}.md"
            filename = filename.replace(' ', '_').replace('\n', '')
        
        output_path = Path("performance_analysis") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 GUI结构分析报告已保存: {output_path}")
        return output_path


class ASTClassAnalyzer(ast.NodeVisitor):
    """AST类分析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.elements = []
        self.current_class = None
    
    def visit_ClassDef(self, node):
        """访问类定义"""
        element = CodeElement(
            name=node.name,
            element_type='class',
            file_path=self.file_path,
            line_number=node.lineno,
            complexity_score=len(node.body)
        )
        
        # 分析类的性能特征
        if 'Window' in node.name or 'Dialog' in node.name:
            element.performance_indicators.append('gui_component')
        
        self.elements.append(element)
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """访问函数定义"""
        element_type = 'method' if self.current_class else 'function'
        
        element = CodeElement(
            name=node.name,
            element_type=element_type,
            file_path=self.file_path,
            line_number=node.lineno,
            complexity_score=self._calculate_complexity(node)
        )
        
        # 分析性能特征
        if node.name.startswith('update_') or node.name.startswith('refresh_'):
            element.performance_indicators.append('frequent_update')
        
        if node.name.startswith('on_') or node.name.startswith('handle_'):
            element.performance_indicators.append('event_handler')
        
        self.elements.append(element)
        self.generic_visit(node)
    
    def _calculate_complexity(self, node) -> int:
        """计算复杂度 (简化的圈复杂度)"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity


if __name__ == "__main__":
    # 运行GUI结构分析
    analyzer = GUIStructureAnalyzer()
    results = analyzer.analyze_gui_structure()
    report_path = analyzer.save_analysis_report()
    
    print(f"\n🎯 分析完成！")
    print(f"📁 报告位置: {report_path}")
    print(f"📊 发现 {len(results['performance_concerns'])} 个性能关注点")
    print(f"🏗️  分析了 {len(results['component_hierarchy'])} 个GUI组件")