"""
Performance and load testing for the DuckDB Macro REST Server.
"""
import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient


class TestPerformance:
    """Performance testing suite."""
    
    def test_single_request_latency(self, test_client: TestClient):
        """Test latency of a single request."""
        start_time = time.time()
        response = test_client.post(
            "/api/v1/macros/greet/execute",
            json={"name": "World"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        latency_ms = (end_time - start_time) * 1000
        print(f"Single request latency: {latency_ms:.2f}ms")
        
        # Should respond within reasonable time (adjust threshold as needed)
        assert latency_ms < 1000  # 1 second
    
    def test_sequential_requests_performance(self, test_client: TestClient):
        """Test performance of sequential requests."""
        request_count = 50
        latencies = []
        
        for i in range(request_count):
            start_time = time.time()
            response = test_client.post(
                "/api/v1/macros/greet/execute",
                json={"name": f"User{i}"}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            latencies.append((end_time - start_time) * 1000)
        
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        print(f"Sequential requests ({request_count}):")
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")
        print(f"  Min latency: {min(latencies):.2f}ms")
        print(f"  Max latency: {max(latencies):.2f}ms")
        
        # Performance assertions
        assert avg_latency < 100  # Average should be under 100ms
        assert p95_latency < 500   # P95 should be under 500ms
    
    def test_concurrent_requests_performance(self, test_client: TestClient):
        """Test performance under concurrent load."""
        request_count = 100
        concurrent_workers = 10
        
        def make_request(worker_id, request_id):
            start_time = time.time()
            response = test_client.post(
                "/api/v1/macros/greet/execute",
                json={"name": f"Worker{worker_id}_Request{request_id}"}
            )
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000
        
        latencies = []
        errors = 0
        
        start_test_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = []
            
            for i in range(request_count):
                worker_id = i % concurrent_workers
                future = executor.submit(make_request, worker_id, i)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    status_code, latency = future.result()
                    if status_code == 200:
                        latencies.append(latency)
                    else:
                        errors += 1
                except Exception:
                    errors += 1
        
        end_test_time = time.time()
        total_test_time = end_test_time - start_test_time
        
        successful_requests = len(latencies)
        throughput = successful_requests / total_test_time
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        else:
            avg_latency = 0
            p95_latency = 0
        
        print(f"Concurrent requests ({request_count} requests, {concurrent_workers} workers):")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Failed requests: {errors}")
        print(f"  Total test time: {total_test_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")
        
        # Performance assertions
        assert errors < request_count * 0.05  # Less than 5% errors
        assert throughput > 10  # At least 10 requests per second
        assert avg_latency < 1000  # Average latency under 1 second
    
    def test_database_query_performance(self, test_client: TestClient):
        """Test performance of database-intensive queries."""
        queries = [
            ("/api/v1/macros/employee_count/execute", {}),
            ("/api/v1/macros/salary_stats/execute", {}),
            ("/api/v1/macros/employees_by_department/execute", {"dept": "Engineering"}),
            ("/api/v1/macros/high_earners/execute", {"min_salary": 60000}),
        ]
        
        for endpoint, params in queries:
            latencies = []
            
            # Run each query multiple times
            for _ in range(10):
                start_time = time.time()
                response = test_client.post(endpoint, json=params)
                end_time = time.time()
                
                assert response.status_code == 200
                latencies.append((end_time - start_time) * 1000)
            
            avg_latency = statistics.mean(latencies)
            print(f"Query {endpoint}: avg {avg_latency:.2f}ms")
            
            # Database queries should be fast
            assert avg_latency < 100  # Under 100ms average
    
    def test_memory_usage_stability(self, test_client: TestClient):
        """Test memory usage stability under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests to test memory stability
        for i in range(200):
            response = test_client.post(
                "/api/v1/macros/greet/execute",
                json={"name": f"User{i}"}
            )
            assert response.status_code == 200
            
            # Check memory every 50 requests
            if i % 50 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"After {i} requests: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # Memory shouldn't grow excessively
                assert memory_increase < 100  # Less than 100MB increase
    
    def test_response_size_performance(self, test_client: TestClient):
        """Test performance with different response sizes."""
        # Test with queries that return different amounts of data
        test_cases = [
            ("employee_count", {}, "Small response"),
            ("salary_stats", {}, "Medium response"),
            ("employees_by_department", {"dept": "Engineering"}, "Large response"),
        ]
        
        for macro_name, params, description in test_cases:
            latencies = []
            response_sizes = []
            
            for _ in range(10):
                start_time = time.time()
                response = test_client.post(
                    f"/api/v1/macros/{macro_name}/execute",
                    json=params
                )
                end_time = time.time()
                
                assert response.status_code == 200
                
                latency = (end_time - start_time) * 1000
                response_size = len(response.content)
                
                latencies.append(latency)
                response_sizes.append(response_size)
            
            avg_latency = statistics.mean(latencies)
            avg_size = statistics.mean(response_sizes)
            
            print(f"{description} ({macro_name}): {avg_latency:.2f}ms, {avg_size:.0f} bytes")
            
            # Latency should be reasonable regardless of response size
            assert avg_latency < 200  # Under 200ms


class TestStressTest:
    """Stress testing to find breaking points."""
    
    @pytest.mark.slow
    def test_sustained_load(self, test_client: TestClient):
        """Test sustained load over time."""
        duration_seconds = 30  # 30 second test
        concurrent_workers = 5
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        request_count = 0
        error_count = 0
        latencies = []
        
        def worker():
            nonlocal request_count, error_count
            worker_request_count = 0
            
            while time.time() < end_time:
                try:
                    req_start = time.time()
                    response = test_client.post(
                        "/api/v1/macros/greet/execute",
                        json={"name": f"LoadTest{worker_request_count}"}
                    )
                    req_end = time.time()
                    
                    if response.status_code == 200:
                        latencies.append((req_end - req_start) * 1000)
                    else:
                        error_count += 1
                    
                    request_count += 1
                    worker_request_count += 1
                    
                except Exception:
                    error_count += 1
                
                # Small delay to prevent overwhelming
                time.sleep(0.01)
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent_workers)]
            
            # Wait for all workers to complete
            for future in as_completed(futures):
                future.result()
        
        actual_duration = time.time() - start_time
        throughput = request_count / actual_duration
        error_rate = error_count / request_count if request_count > 0 else 0
        
        avg_latency = statistics.mean(latencies) if latencies else 0
        
        print(f"Sustained load test ({duration_seconds}s):")
        print(f"  Total requests: {request_count}")
        print(f"  Errors: {error_count} ({error_rate:.2%})")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  Average latency: {avg_latency:.2f}ms")
        
        # Stress test assertions
        assert error_rate < 0.1  # Less than 10% errors under sustained load
        assert throughput > 5     # At least 5 req/s sustained
        assert avg_latency < 2000  # Average latency under 2 seconds
    
    @pytest.mark.slow
    def test_connection_limit(self, test_client: TestClient):
        """Test behavior at connection limits."""
        # This test tries to find the connection limit
        max_concurrent = 50
        
        def make_long_request():
            # Use a query that takes a bit longer
            return test_client.post(
                "/api/v1/macros/salary_stats/execute",
                json={}
            )
        
        successful_requests = 0
        failed_requests = 0
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [executor.submit(make_long_request) for _ in range(max_concurrent)]
            
            for future in as_completed(futures):
                try:
                    response = future.result(timeout=10)
                    if response.status_code == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                except Exception:
                    failed_requests += 1
        
        print(f"Connection limit test ({max_concurrent} concurrent):")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        
        # Should handle reasonable number of concurrent connections
        assert successful_requests > max_concurrent * 0.8  # At least 80% success rate


# Mark slow tests - skip by default
slow = pytest.mark.skipif(
    True,  # Skip slow tests by default 
    reason="Slow tests skipped by default. Use pytest -m 'not slow' to run fast tests only."
)
