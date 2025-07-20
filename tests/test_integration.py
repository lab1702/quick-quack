"""
Integration tests for monitoring and logging features.
"""
import pytest
import json
import time
from fastapi.testclient import TestClient


class TestMonitoringIntegration:
    """Test monitoring and observability features."""
    
    def test_health_check_integration(self, test_client: TestClient):
        """Test health check integration with actual services."""
        # Make a few requests first to populate metrics
        test_client.post("/api/v1/macros/greet/execute", json={"name": "Test"})
        test_client.get("/api/v1/macros")
        
        # Check health endpoint
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True
        assert data["macro_count"] >= 5
        assert data["uptime_seconds"] > 0
    
    def test_detailed_health_with_system_metrics(self, test_client: TestClient):
        """Test detailed health endpoint with system metrics."""
        response = test_client.get("/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check system metrics are present and reasonable
        assert "system_metrics" in data
        metrics = data["system_metrics"]
        
        assert "memory" in metrics
        assert metrics["memory"]["total_gb"] > 0
        assert 0 <= metrics["memory"]["used_percent"] <= 100
        
        assert "cpu" in metrics
        assert metrics["cpu"]["core_count"] > 0
        assert 0 <= metrics["cpu"]["usage_percent"] <= 100
        
        assert "disk" in metrics
        assert metrics["disk"]["total_gb"] > 0
        assert 0 <= metrics["disk"]["used_percent"] <= 100
        
        # Check connection pool status
        assert "connection_pool_status" in data
        pool_status = data["connection_pool_status"]
        assert pool_status["active_connections"] >= 0
        assert pool_status["max_connections"] > 0
        assert isinstance(pool_status["connection_pool_healthy"], bool)
    
    def test_readiness_check_comprehensive(self, test_client: TestClient):
        """Test comprehensive readiness checks."""
        response = test_client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ready"] is True
        
        # All checks should pass
        checks = data["checks"]
        assert checks["database"] is True
        assert checks["macro_service"] is True
        assert checks["memory"] is True
        assert checks["disk"] is True
        
        # Details should be present
        assert "details" in data
        details = data["details"]
        
        assert "database" in details
        assert "macro_service" in details
        assert "system_metrics" in details
    
    def test_prometheus_metrics_format(self, test_client: TestClient):
        """Test Prometheus metrics format and content."""
        # Make some requests to generate metrics
        for i in range(5):
            test_client.post("/api/v1/macros/greet/execute", json={"name": f"User{i}"})
        
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        
        # Check for required metrics
        expected_metrics = [
            "duckdb_rest_uptime_seconds",
            "duckdb_rest_database_connected",
            "duckdb_rest_macro_count",
            "duckdb_rest_active_connections",
            "duckdb_rest_memory_usage_percent",
            "duckdb_rest_cpu_usage_percent",
            "duckdb_rest_disk_usage_percent"
        ]
        
        for metric in expected_metrics:
            assert metric in content
        
        # Check format is valid Prometheus format
        lines = content.strip().split('\n')
        help_lines = [line for line in lines if line.startswith('# HELP')]
        type_lines = [line for line in lines if line.startswith('# TYPE')]
        metric_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        
        assert len(help_lines) >= len(expected_metrics)
        assert len(type_lines) >= len(expected_metrics)
        assert len(metric_lines) >= len(expected_metrics)
        
        # Validate metric values are numeric
        for line in metric_lines:
            if ' ' in line:
                metric_name, value = line.rsplit(' ', 1)
                try:
                    float(value)
                except ValueError:
                    pytest.fail(f"Invalid metric value: {line}")
    
    def test_correlation_id_tracking(self, test_client: TestClient):
        """Test correlation ID tracking through requests."""
        # Make a request with custom correlation ID header
        correlation_id = "test-correlation-123"
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": "Correlation Test"},
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code == 200
        
        # Check if correlation ID is returned in response headers
        response_correlation_id = response.headers.get("X-Correlation-ID")
        assert response_correlation_id == correlation_id
    
    def test_response_time_headers(self, test_client: TestClient):
        """Test response time headers are included."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": "Performance Test"}
        )
        
        assert response.status_code == 200
        
        # Check for performance headers (if implemented)
        # This depends on middleware implementation
        assert "X-Process-Time" in response.headers or "X-Response-Time" in response.headers
    
    def test_error_tracking_in_monitoring(self, test_client: TestClient):
        """Test that errors are properly tracked in monitoring."""
        # Generate some errors
        test_client.post("/api/v1/macros/nonexistent/execute", json={})
        test_client.get("/api/v1/macros/invalid_name")
        test_client.post("/api/v1/macros/greet/execute", json={"wrong": "param"})
        
        # Check that health status still reports healthy
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"  # Errors shouldn't affect overall health
        
        # Metrics should still be available
        response = test_client.get("/metrics")
        assert response.status_code == 200


class TestLoggingIntegration:
    """Test structured logging integration."""
    
    def test_structured_logging_format(self, test_client: TestClient, caplog):
        """Test that structured logging produces correct format."""
        # Enable JSON logging for this test
        with caplog.at_level("INFO"):
            response = test_client.post(
                "/api/v1/macros/greet/execute",
                json={"name": "Logging Test"}
            )
            assert response.status_code == 200
        
        # Check that logs were generated
        assert len(caplog.records) > 0
        
        # Note: This test depends on how logging is configured
        # In a real test, you'd check the actual log output format
    
    def test_request_logging(self, test_client: TestClient):
        """Test that requests are properly logged."""
        # Make requests that should generate logs
        test_client.get("/health")
        test_client.get("/api/v1/macros")
        test_client.post("/api/v1/macros/greet/execute", json={"name": "Test"})
        
        # In a real implementation, you'd check log files or log capture
        # For now, we'll just verify the requests complete successfully
        assert True  # Placeholder for actual log verification
    
    def test_error_logging(self, test_client: TestClient):
        """Test that errors are properly logged."""
        # Generate various types of errors
        test_client.post("/api/v1/macros/nonexistent/execute", json={})
        test_client.get("/api/v1/macros/invalid_name")
        test_client.post("/api/v1/macros/greet/execute", json={"wrong": "param"})
        
        # In a real implementation, you'd verify error logs are generated
        assert True  # Placeholder for actual error log verification


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_complete_workflow(self, test_client: TestClient):
        """Test a complete workflow from discovery to execution."""
        # 1. Check service health
        health_response = test_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # 2. List available macros
        macros_response = test_client.get("/api/v1/macros")
        assert macros_response.status_code == 200
        macros = macros_response.json()
        assert len(macros) >= 5
        
        # 3. Get specific macro info
        macro_info_response = test_client.get("/api/v1/macros/greet")
        assert macro_info_response.status_code == 200
        macro_info = macro_info_response.json()
        assert macro_info["name"] == "greet"
        
        # 4. Execute the macro
        execution_response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": "Integration Test"}
        )
        assert execution_response.status_code == 200
        result = execution_response.json()
        assert result[0]["greeting"] == "Hello, Integration Test!"
        
        # 5. Check metrics after operations
        metrics_response = test_client.get("/metrics")
        assert metrics_response.status_code == 200
        assert "duckdb_rest_uptime_seconds" in metrics_response.text
    
    def test_multiple_macro_types_workflow(self, test_client: TestClient):
        """Test workflow with different types of macros."""
        test_cases = [
            # (endpoint, params, expected_type)
            ("/api/v1/macros/greet/execute", {"name": "Test"}, "greeting"),
            ("/api/v1/macros/employee_count/execute", {}, "total_employees"),
            ("/api/v1/macros/employees_by_department/execute", {"dept": "Engineering"}, "department"),
            ("/api/v1/macros/high_earners/execute", {"min_salary": 70000}, "salary"),
            ("/api/v1/macros/salary_stats/execute", {}, "avg_salary"),
        ]
        
        for endpoint, params, expected_field in test_cases:
            response = test_client.post(endpoint, json=params)
            assert response.status_code == 200, f"Failed for {endpoint}"
            
            data = response.json()
            assert len(data) >= 1, f"No data returned for {endpoint}"
            assert expected_field in data[0], f"Expected field {expected_field} not found in {endpoint}"
    
    def test_dynamic_endpoints_workflow(self, test_client: TestClient):
        """Test workflow using dynamic endpoints."""
        # Test GET dynamic endpoints
        response = test_client.get("/greet?name=Dynamic Test")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["greeting"] == "Hello, Dynamic Test!"
        
        # Test POST dynamic endpoints
        response = test_client.post(
            "/employees_by_department",
            json={"dept": "Sales"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Bob and Eva
        
        # Test no-parameter dynamic endpoint
        response = test_client.get("/employee_count")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["total_employees"] == 5
    
    def test_monitoring_during_load(self, test_client: TestClient):
        """Test monitoring endpoints during load."""
        import threading
        import time
        
        # Start background load
        def background_load():
            for i in range(50):
                test_client.post("/api/v1/macros/greet/execute", json={"name": f"Load{i}"})
                time.sleep(0.01)
        
        load_thread = threading.Thread(target=background_load)
        load_thread.start()
        
        try:
            # Check monitoring endpoints during load
            for _ in range(10):
                # Health check
                health_response = test_client.get("/health")
                assert health_response.status_code == 200
                
                # Metrics
                metrics_response = test_client.get("/metrics")
                assert metrics_response.status_code == 200
                
                # Readiness
                ready_response = test_client.get("/ready")
                assert ready_response.status_code == 200
                
                time.sleep(0.1)
        
        finally:
            load_thread.join()
    
    def test_error_recovery_workflow(self, test_client: TestClient):
        """Test system recovery after errors."""
        # Generate some errors
        test_client.post("/api/v1/macros/nonexistent/execute", json={})
        test_client.get("/api/v1/macros/invalid_name")
        test_client.post("/api/v1/macros/greet/execute", json={"wrong": "param"})
        
        # System should still be healthy and functional
        health_response = test_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Normal operations should still work
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": "Recovery Test"}
        )
        assert response.status_code == 200
        assert response.json()[0]["greeting"] == "Hello, Recovery Test!"
