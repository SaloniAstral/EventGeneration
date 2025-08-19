#!/usr/bin/env python3
"""
Health Checker - System Health Monitoring
========================================

This file monitors the health of all system components:
- Checks if all EC2 instances are running
- Monitors database connections
- Verifies API endpoints are responding
- Tests external service connections
- Reports system status and alerts

Think of this as the "doctor" that checks if everything is working properly.
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.config import MonitoringConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health checker for all system components"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: Dict = {}
    
    async def start(self):
        """Start the health checker"""
        self.session = aiohttp.ClientSession()
        logger.info("🏥 Health checker started")
    
    async def stop(self):
        """Stop the health checker"""
        if self.session:
            await self.session.close()
        logger.info("🛑 Health checker stopped")
    
    async def check_all_services(self) -> Dict:
        """Check health of all services"""
        logger.info("🔍 Checking all services...")
        
        tasks = []
        for service_name, url in MonitoringConfig.get_all_service_urls().items():
            tasks.append(self.check_service_health(service_name, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (service_name, _) in enumerate(MonitoringConfig.get_all_service_urls().items()):
            if isinstance(results[i], Exception):
                self.results[service_name] = {
                    "status": "error",
                    "error": str(results[i]),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.results[service_name] = results[i]
        
        return self.results
    
    async def check_service_health(self, service_name: str, url: str) -> Dict:
        """Check health of a specific service"""
        start_time = time.time()
        try:
            # Check basic health endpoint
            async with self.session.get(f"{url}/health", timeout=10) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "status": "healthy",
                        "response_time": response_time,
                        "data": health_data,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time": response_time,
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "response_time": time.time() - start_time,
                "error": "Request timeout",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "response_time": time.time() - start_time,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_database_health(self) -> Dict:
        """Check database health"""
        logger.info("🗄️ Checking database health...")
        
        try:
            # Check API server database stats
            api_url = MonitoringConfig.get_service_url("api_server")
            async with self.session.get(f"{api_url}/api/v1/database/health", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"Database health check failed: HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Database health check error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_stream_health(self) -> Dict:
        """Check stream processing health"""
        logger.info("🌊 Checking stream processing health...")
        
        try:
            # Check stream receiver performance
            stream_url = MonitoringConfig.get_service_url("stream_receiver")
            async with self.session.get(f"{stream_url}/api/v1/stream/performance", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"Stream health check failed: HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Stream health check error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_event_system_health(self) -> Dict:
        """Check event system health"""
        logger.info("📡 Checking event system health...")
        
        try:
            # Check event system stats
            api_url = MonitoringConfig.get_service_url("api_server")
            async with self.session.get(f"{api_url}/api/v1/events/stats", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"Event system health check failed: HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Event system health check error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_external_dependencies(self) -> Dict:
        """Check external dependencies"""
        logger.info("🔗 Checking external dependencies...")
        
        results = {}
        
        # Check Alpha Vantage API (via our API server)
        try:
            api_url = MonitoringConfig.get_service_url("api_server")
            async with self.session.get(f"{api_url}/status", timeout=10) as response:
                if response.status == 200:
                    status_data = await response.json()
                    results["alpha_vantage"] = {
                        "status": "healthy" if status_data.get("alpha_vantage_connection") else "error",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    results["alpha_vantage"] = {
                        "status": "error",
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            results["alpha_vantage"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # Check AWS SNS (via our API server)
        try:
            api_url = MonitoringConfig.get_service_url("api_server")
            async with self.session.get(f"{api_url}/status", timeout=10) as response:
                if response.status == 200:
                    status_data = await response.json()
                    results["aws_sns"] = {
                        "status": "healthy" if status_data.get("sns_connection") else "error",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    results["aws_sns"] = {
                        "status": "error",
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            results["aws_sns"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        return results
    
    async def comprehensive_health_check(self) -> Dict:
        """Perform comprehensive health check of entire system"""
        logger.info("🏥 Starting comprehensive health check...")
        
        await self.start()
        
        try:
            # Check all components
            services_health = await self.check_all_services()
            database_health = await self.check_database_health()
            stream_health = await self.check_stream_health()
            event_health = await self.check_event_system_health()
            external_health = await self.check_external_dependencies()
            
            # Compile comprehensive results
            comprehensive_results = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "services": services_health,
                "database": database_health,
                "stream_processing": stream_health,
                "event_system": event_health,
                "external_dependencies": external_health,
                "summary": {
                    "total_services": len(services_health),
                    "healthy_services": len([s for s in services_health.values() if s.get("status") == "healthy"]),
                    "unhealthy_services": len([s for s in services_health.values() if s.get("status") != "healthy"]),
                    "database_status": database_health.get("status", "unknown"),
                    "stream_status": stream_health.get("status", "unknown"),
                    "event_system_status": event_health.get("status", "unknown")
                }
            }
            
            # Determine overall status
            unhealthy_count = comprehensive_results["summary"]["unhealthy_services"]
            if unhealthy_count == 0:
                comprehensive_results["overall_status"] = "healthy"
            elif unhealthy_count <= 1:
                comprehensive_results["overall_status"] = "warning"
            else:
                comprehensive_results["overall_status"] = "critical"
            
            return comprehensive_results
            
        finally:
            await self.stop()
    
    def print_health_report(self, results: Dict):
        """Print a formatted health report"""
        print("\n" + "="*80)
        print("🏥 FINANCIAL DATA STREAMING SYSTEM - HEALTH REPORT")
        print("="*80)
        print(f"📅 Timestamp: {results['timestamp']}")
        print(f"🎯 Overall Status: {results['overall_status'].upper()}")
        print()
        
        # Services summary
        print("📊 SERVICES SUMMARY:")
        summary = results.get("summary", {})
        print(f"   Total Services: {summary.get('total_services', 0)}")
        print(f"   Healthy: {summary.get('healthy_services', 0)}")
        print(f"   Unhealthy: {summary.get('unhealthy_services', 0)}")
        print()
        
        # Individual service status
        print("🔍 INDIVIDUAL SERVICE STATUS:")
        for service_name, health in results.get("services", {}).items():
            status = health.get("status", "unknown")
            status_icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
            response_time = health.get("response_time", 0)
            print(f"   {status_icon} {service_name}: {status.upper()} ({response_time:.2f}s)")
        print()
        
        # Component status
        print("🏗️ COMPONENT STATUS:")
        components = [
            ("Database", results.get("database", {})),
            ("Stream Processing", results.get("stream_processing", {})),
            ("Event System", results.get("event_system", {}))
        ]
        
        for component_name, component_health in components:
            status = component_health.get("status", "unknown")
            status_icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
            print(f"   {status_icon} {component_name}: {status.upper()}")
        print()
        
        # External dependencies
        print("🔗 EXTERNAL DEPENDENCIES:")
        for dep_name, dep_health in results.get("external_dependencies", {}).items():
            status = dep_health.get("status", "unknown")
            status_icon = "✅" if status == "healthy" else "❌"
            print(f"   {status_icon} {dep_name}: {status.upper()}")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if results["overall_status"] == "healthy":
            print("   ✅ System is healthy and operating normally")
        elif results["overall_status"] == "warning":
            print("   ⚠️ Some services have issues - monitor closely")
        else:
            print("   🚨 Critical issues detected - immediate attention required")
        
        print("="*80)

async def main():
    """Main function to run health check"""
    checker = HealthChecker()
    
    try:
        results = await checker.comprehensive_health_check()
        checker.print_health_report(results)
        
        # Return appropriate exit code
        if results["overall_status"] == "healthy":
            sys.exit(0)
        elif results["overall_status"] == "warning":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"❌ Health check failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main()) 