"""
Integration tests for the REST API endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""
    
    def test_health_endpoint(self, test_client: TestClient):
        """Test basic health endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert data["database_connected"] is True
        assert "macro_count" in data
        assert data["macro_count"] >= 5
    
    def test_detailed_health_endpoint(self, test_client: TestClient):
        """Test detailed health endpoint with system metrics."""
        response = test_client.get("/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "system_metrics" in data
        assert "memory" in data["system_metrics"]
        assert "cpu" in data["system_metrics"]
        assert "disk" in data["system_metrics"]
        assert "connection_pool_status" in data
    
    def test_readiness_endpoint(self, test_client: TestClient):
        """Test readiness endpoint."""
        response = test_client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data
        assert data["checks"]["database"] is True
        assert data["checks"]["macro_service"] is True
    
    def test_metrics_endpoint(self, test_client: TestClient):
        """Test Prometheus metrics endpoint."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        
        # Should return Prometheus format text
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        content = response.text
        
        # Check for expected metrics
        assert "duckdb_rest_uptime_seconds" in content
        assert "duckdb_rest_database_connected" in content
        assert "duckdb_rest_macro_count" in content


class TestMacroListEndpoints:
    """Test macro listing endpoints."""
    
    def test_list_macros(self, test_client: TestClient):
        """Test listing all macros."""
        response = test_client.get("/api/v1/macros")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        
        # Check structure of macro info
        for macro in data:
            assert "name" in macro
            assert "parameters" in macro
            assert "parameter_types" in macro
            assert "return_type" in macro
            assert "macro_type" in macro
    
    def test_get_specific_macro_info(self, test_client: TestClient):
        """Test getting information for a specific macro."""
        response = test_client.get("/api/v1/macros/greet")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "greet"
        assert len(data["parameters"]) == 1
        assert data["parameters"][0] == "name"
    
    def test_get_nonexistent_macro_info(self, test_client: TestClient):
        """Test getting info for a macro that doesn't exist."""
        response = test_client.get("/api/v1/macros/nonexistent_macro")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestMacroExecutionEndpoints:
    """Test macro execution endpoints."""
    
    def test_execute_simple_macro(self, test_client: TestClient):
        """Test executing a simple macro."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": "World"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["greeting"] == "Hello, World!"
    
    def test_execute_macro_no_params(self, test_client: TestClient):
        """Test executing a macro with no parameters."""
        response = test_client.post(
            "/api/v1/macros/employee_count/execute",
            json={}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_employees"] == 5
    
    def test_execute_macro_with_filtering(self, test_client: TestClient):
        """Test executing a macro that filters data."""
        response = test_client.post(
            "/api/v1/macros/employees_by_department/execute",
            json={"dept": "Engineering"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2  # Alice and Carol
        
        for employee in data:
            assert employee["department"] == "Engineering"
    
    def test_execute_macro_with_numeric_param(self, test_client: TestClient):
        """Test executing a macro with numeric parameters."""
        response = test_client.post(
            "/api/v1/macros/high_earners/execute",
            json={"min_salary": 70000}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3  # Employees earning 70k or more
        
        for employee in data:
            assert employee["salary"] >= 70000
    
    def test_execute_nonexistent_macro(self, test_client: TestClient):
        """Test executing a macro that doesn't exist."""
        response = test_client.post(
            "/api/v1/macros/nonexistent_macro/execute",
            json={}
        )
        assert response.status_code == 404
    
    def test_execute_macro_wrong_parameters(self, test_client: TestClient):
        """Test executing a macro with wrong parameters."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"wrong_param": "value"}
        )
        assert response.status_code == 400
    
    def test_execute_macro_missing_parameters(self, test_client: TestClient):
        """Test executing a macro with missing required parameters."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={}
        )
        assert response.status_code == 400
    
    def test_execute_macro_invalid_json(self, test_client: TestClient):
        """Test executing a macro with invalid JSON."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422


class TestDynamicEndpoints:
    """Test dynamically generated endpoints for macros."""
    
    def test_dynamic_get_endpoint_simple(self, test_client: TestClient):
        """Test dynamic GET endpoint for simple macro."""
        response = test_client.get("/greet?name=World")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["greeting"] == "Hello, World!"
    
    def test_dynamic_get_endpoint_no_params(self, test_client: TestClient):
        """Test dynamic GET endpoint for macro with no parameters."""
        response = test_client.get("/employee_count")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_employees"] == 5
    
    def test_dynamic_post_endpoint(self, test_client: TestClient):
        """Test dynamic POST endpoint for macro."""
        response = test_client.post(
            "/employees_by_department",
            json={"dept": "Sales"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2  # Bob and Eva
        
        for employee in data:
            assert employee["department"] == "Sales"
    
    def test_dynamic_endpoint_missing_params(self, test_client: TestClient):
        """Test dynamic endpoint with missing parameters."""
        response = test_client.get("/greet")  # Missing required 'name' parameter
        assert response.status_code == 422
    
    def test_dynamic_endpoint_invalid_macro(self, test_client: TestClient):
        """Test dynamic endpoint for non-existent macro."""
        response = test_client.get("/nonexistent_macro")
        assert response.status_code == 404


class TestSecurityAndValidation:
    """Test security and input validation."""
    
    def test_sql_injection_protection(self, test_client: TestClient):
        """Test protection against SQL injection attempts."""
        malicious_inputs = [
            "'; DROP TABLE employees; --",
            "' OR '1'='1",
            "'; DELETE FROM employees; --",
        ]
        
        for malicious_input in malicious_inputs:
            response = test_client.post(
                "/api/v1/macros/greet/execute",
                json={"name": malicious_input}
            )
            # Should either reject the input or handle it safely
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                # If accepted, should be treated as literal string
                data = response.json()
                assert malicious_input in data[0]["greeting"]
    
    def test_macro_name_validation(self, test_client: TestClient):
        """Test validation of macro names in URLs."""
        invalid_names = [
            "../../../etc/passwd",
            "DROP%20TABLE%20employees",
            "macro with spaces",
            "macro-with-dashes"
        ]
        
        for invalid_name in invalid_names:
            response = test_client.get(f"/api/v1/macros/{invalid_name}")
            assert response.status_code in [400, 404, 422]
    
    def test_parameter_size_limits(self, test_client: TestClient):
        """Test handling of large parameter values."""
        large_string = "x" * 10000  # 10KB string
        
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": large_string}
        )
        
        # Should either handle it or reject gracefully
        assert response.status_code in [200, 400, 413, 422]
    
    def test_concurrent_requests(self, test_client: TestClient):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(worker_id):
            try:
                response = test_client.post(
                    "/api/v1/macros/greet/execute",
                    json={"name": f"Worker{worker_id}"}
                )
                results.append((worker_id, response.status_code, response.json()))
                time.sleep(0.1)
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent requests: {errors}"
        assert len(results) == 10
        
        for worker_id, status_code, data in results:
            assert status_code == 200
            assert data[0]["greeting"] == f"Hello, Worker{worker_id}!"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_content_type(self, test_client: TestClient):
        """Test handling of invalid content types."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            data="name=World",
            headers={"content-type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422
    
    def test_empty_request_body(self, test_client: TestClient):
        """Test handling of empty request body."""
        response = test_client.post(
            "/api/v1/macros/employee_count/execute"
        )
        assert response.status_code == 200  # Should work for macros with no params
    
    def test_malformed_json(self, test_client: TestClient):
        """Test handling of malformed JSON."""
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            data='{"name": "World"',  # Missing closing brace
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_unsupported_http_methods(self, test_client: TestClient):
        """Test unsupported HTTP methods."""
        # PUT should not be allowed
        response = test_client.put("/api/v1/macros/greet/execute")
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = test_client.delete("/api/v1/macros/greet")
        assert response.status_code == 405
