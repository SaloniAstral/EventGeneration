#!/usr/bin/env python3
"""
Metrics Collector - Performance Data Collection
==============================================

This file collects performance metrics from all system components:
- Gathers data processing statistics
- Monitors streaming performance
- Tracks API response times
- Collects error rates and success metrics
- Aggregates data for dashboard display

Think of this as the "data collector" that gathers performance information.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InstanceMetrics:
    """Metrics for a single EC2 instance"""
    instance_id: str
    cpu_usage: float
    memory_usage: float
    network_in: float
    network_out: float
    disk_usage: float
    timestamp: str

@dataclass
class DataFlowMetrics:
    """Metrics for data flow"""
    ticks_processed: int
    ticks_per_second: float
    average_latency: float
    error_rate: float
    buffer_size: int
    kafka_lag: int
    timestamp: str

class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self, window_size: int = 3600):  # 1 hour window
        self.instance_metrics: Dict[str, List[InstanceMetrics]] = {
            'ec2_fetcher': deque(maxlen=window_size),
            'ec2_driver': deque(maxlen=window_size),
            'ec2_processor': deque(maxlen=window_size)
        }
        self.data_flow_metrics = deque(maxlen=window_size)
        self.error_counts: Dict[str, int] = {
            'fetch_errors': 0,
            'processing_errors': 0,
            'connection_errors': 0
        }
        self.start_time = time.time()
        
    def record_instance_metrics(self, instance_id: str, metrics: InstanceMetrics):
        """Record metrics for an EC2 instance"""
        if instance_id in self.instance_metrics:
            self.instance_metrics[instance_id].append(metrics)
            logger.debug(f"📊 Recorded metrics for {instance_id}")
    
    def record_data_flow(self, metrics: DataFlowMetrics):
        """Record data flow metrics"""
        self.data_flow_metrics.append(metrics)
        logger.debug("📈 Recorded data flow metrics")
    
    def record_error(self, error_type: str):
        """Record an error occurrence"""
        if error_type in self.error_counts:
            self.error_counts[error_type] += 1
            logger.warning(f"⚠️ Recorded error: {error_type}")
    
    def get_instance_metrics(self, instance_id: str, duration: int = 300) -> List[InstanceMetrics]:
        """Get metrics for an instance over the last N seconds"""
        if instance_id not in self.instance_metrics:
            return []
            
        current_time = time.time()
        return [
            metric for metric in self.instance_metrics[instance_id]
            if current_time - time.mktime(datetime.fromisoformat(metric.timestamp).timetuple()) <= duration
        ]
    
    def get_data_flow_metrics(self, duration: int = 300) -> List[DataFlowMetrics]:
        """Get data flow metrics over the last N seconds"""
        current_time = time.time()
        return [
            metric for metric in self.data_flow_metrics
            if current_time - time.mktime(datetime.fromisoformat(metric.timestamp).timetuple()) <= duration
        ]
    
    def get_error_rates(self, duration: int = 300) -> Dict[str, float]:
        """Calculate error rates over the last N seconds"""
        total_time = time.time() - self.start_time
        rates = {}
        
        for error_type, count in self.error_counts.items():
            rates[error_type] = count / (total_time / 60)  # errors per minute
            
        return rates
    
    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        try:
            recent_metrics = self.get_data_flow_metrics(300)  # Last 5 minutes
            
            if not recent_metrics:
                return {
                    'status': 'unknown',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Calculate averages
            avg_tps = sum(m.ticks_per_second for m in recent_metrics) / len(recent_metrics)
            avg_latency = sum(m.average_latency for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
            
            # Determine system health
            status = 'healthy'
            if avg_error_rate > 0.05:  # More than 5% error rate
                status = 'degraded'
            if avg_error_rate > 0.15:  # More than 15% error rate
                status = 'unhealthy'
            
            return {
                'status': status,
                'average_tps': avg_tps,
                'average_latency': avg_latency,
                'error_rate': avg_error_rate,
                'buffer_size': recent_metrics[-1].buffer_size,
                'kafka_lag': recent_metrics[-1].kafka_lag,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system health: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict:
        """Get detailed performance metrics"""
        try:
            metrics = {
                'instances': {},
                'data_flow': {
                    'current_tps': 0,
                    'peak_tps': 0,
                    'total_ticks': 0,
                    'average_latency': 0
                },
                'errors': self.get_error_rates(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Instance metrics
            for instance_id in self.instance_metrics:
                recent = self.get_instance_metrics(instance_id, 60)  # Last minute
                if recent:
                    metrics['instances'][instance_id] = {
                        'cpu': sum(m.cpu_usage for m in recent) / len(recent),
                        'memory': sum(m.memory_usage for m in recent) / len(recent),
                        'network_in': sum(m.network_in for m in recent) / len(recent),
                        'network_out': sum(m.network_out for m in recent) / len(recent)
                    }
            
            # Data flow metrics
            recent_flow = self.get_data_flow_metrics(60)  # Last minute
            if recent_flow:
                metrics['data_flow'] = {
                    'current_tps': recent_flow[-1].ticks_per_second,
                    'peak_tps': max(m.ticks_per_second for m in recent_flow),
                    'total_ticks': sum(m.ticks_processed for m in recent_flow),
                    'average_latency': sum(m.average_latency for m in recent_flow) / len(recent_flow)
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector