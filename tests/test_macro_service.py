"""
Unit tests for the macro service.
"""
import pytest
from app.macro_service import MacroIntrospectionService
from app.models import MacroInfo


class TestMacroIntrospectionService:
    """Test suite for MacroIntrospectionService class."""
    
    @pytest.mark.asyncio
    async def test_list_macros(self, test_macro_service: MacroIntrospectionService):
        """Test listing all available macros."""
        macros = await test_macro_service.list_macros()
        
        assert len(macros) >= 5  # We created 5 test macros
        
        # Check that we have the expected macros
        macro_names = [macro.name for macro in macros]
        expected_macros = ["greet", "employees_by_department", "high_earners", "employee_count", "salary_stats"]
        
        for expected_macro in expected_macros:
            assert expected_macro in macro_names
    
    @pytest.mark.asyncio
    async def test_macro_info_structure(self, test_macro_service: MacroIntrospectionService):
        """Test that macro info has correct structure."""
        macros = await test_macro_service.list_macros()
        
        for macro in macros:
            assert isinstance(macro, MacroInfo)
            assert hasattr(macro, 'name')
            assert hasattr(macro, 'parameters')
            assert hasattr(macro, 'parameter_types')
            assert hasattr(macro, 'return_type')
            assert hasattr(macro, 'macro_type')
            
            # Basic validation
            assert isinstance(macro.name, str)
            assert len(macro.name) > 0
            assert isinstance(macro.parameters, list)
            assert isinstance(macro.parameter_types, list)
    
    @pytest.mark.asyncio
    async def test_get_macro_info(self, test_macro_service: MacroIntrospectionService):
        """Test getting information for a specific macro."""
        macro_info = await test_macro_service.get_macro_info("greet")
        
        assert macro_info is not None
        assert macro_info.name == "greet"
        assert len(macro_info.parameters) == 1
        assert macro_info.parameters[0] == "name"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_macro_info(self, test_macro_service: MacroIntrospectionService):
        """Test getting info for a macro that doesn't exist."""
        macro_info = await test_macro_service.get_macro_info("nonexistent_macro")
        assert macro_info is None
    
    @pytest.mark.asyncio
    async def test_execute_macro_simple(self, test_macro_service: MacroIntrospectionService):
        """Test executing a simple macro with parameters."""
        result = await test_macro_service.execute_macro("greet", {"name": "World"})
        
        assert len(result) == 1
        assert "greeting" in result[0]
        assert result[0]["greeting"] == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_execute_macro_no_params(self, test_macro_service: MacroIntrospectionService):
        """Test executing a macro with no parameters."""
        result = await test_macro_service.execute_macro("employee_count", {})
        
        assert len(result) == 1
        assert "total_employees" in result[0]
        assert result[0]["total_employees"] == 5
    
    @pytest.mark.asyncio
    async def test_execute_macro_with_data_filtering(self, test_macro_service: MacroIntrospectionService):
        """Test executing a macro that filters data."""
        result = await test_macro_service.execute_macro("employees_by_department", {"dept": "Engineering"})
        
        assert len(result) == 2  # Alice and Carol are in Engineering
        
        # Check that all results are from Engineering department
        for row in result:
            assert row["department"] == "Engineering"
    
    @pytest.mark.asyncio
    async def test_execute_macro_with_numeric_param(self, test_macro_service: MacroIntrospectionService):
        """Test executing a macro with numeric parameters."""
        result = await test_macro_service.execute_macro("high_earners", {"min_salary": 70000})
        
        assert len(result) == 3  # Alice (75k), Carol (80k), Eva (70k)
        
        # Check that all results have salary >= 70000
        for row in result:
            assert row["salary"] >= 70000
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_macro(self, test_macro_service: MacroIntrospectionService):
        """Test executing a macro that doesn't exist."""
        with pytest.raises(Exception):
            await test_macro_service.execute_macro("nonexistent_macro", {})
    
    @pytest.mark.asyncio
    async def test_execute_macro_wrong_parameters(self, test_macro_service: MacroIntrospectionService):
        """Test executing a macro with wrong parameters."""
        with pytest.raises(Exception):
            await test_macro_service.execute_macro("greet", {"wrong_param": "value"})
    
    @pytest.mark.asyncio
    async def test_execute_macro_missing_parameters(self, test_macro_service: MacroIntrospectionService):
        """Test executing a macro with missing required parameters."""
        with pytest.raises(Exception):
            await test_macro_service.execute_macro("greet", {})
    
    @pytest.mark.asyncio
    async def test_cache_macros(self, test_macro_service: MacroIntrospectionService):
        """Test macro caching functionality."""
        # Cache should be empty initially
        assert len(test_macro_service._macro_cache) == 0
        
        # Cache macros
        await test_macro_service.cache_macros()
        
        # Cache should now contain macros
        assert len(test_macro_service._macro_cache) >= 5
        
        # Test that cached macros are accessible
        cached_macro = test_macro_service._macro_cache.get("greet")
        assert cached_macro is not None
        assert cached_macro.name == "greet"
    
    @pytest.mark.asyncio
    async def test_macro_validation(self, test_macro_service: MacroIntrospectionService):
        """Test macro name validation."""
        # Valid macro names
        assert test_macro_service._is_valid_macro_name("greet")
        assert test_macro_service._is_valid_macro_name("employee_count")
        assert test_macro_service._is_valid_macro_name("test_macro_123")
        
        # Invalid macro names
        assert not test_macro_service._is_valid_macro_name("invalid-name")
        assert not test_macro_service._is_valid_macro_name("name with spaces")
        assert not test_macro_service._is_valid_macro_name("DROP TABLE")
        assert not test_macro_service._is_valid_macro_name("")
        assert not test_macro_service._is_valid_macro_name("'; DROP TABLE employees; --")
    
    @pytest.mark.asyncio
    async def test_parameter_type_inference(self, test_macro_service: MacroIntrospectionService):
        """Test parameter type inference for macros."""
        macro_info = await test_macro_service.get_macro_info("high_earners")
        
        assert macro_info is not None
        assert len(macro_info.parameter_types) == 1
        # Parameter type should be inferred (might be VARCHAR or similar)
        assert len(macro_info.parameter_types[0]) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_macro_execution(self, test_macro_service: MacroIntrospectionService):
        """Test concurrent execution of macros."""
        import asyncio
        
        async def execute_greet(name: str):
            result = await test_macro_service.execute_macro("greet", {"name": name})
            return result[0]["greeting"]
        
        # Execute multiple macros concurrently
        tasks = [
            execute_greet("Alice"),
            execute_greet("Bob"),
            execute_greet("Carol"),
            execute_greet("David"),
            execute_greet("Eva")
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert "Hello, Alice!" in results
        assert "Hello, Bob!" in results
        assert "Hello, Carol!" in results
        assert "Hello, David!" in results
        assert "Hello, Eva!" in results


class TestMacroIntrospectionServiceErrorHandling:
    """Test error handling in MacroIntrospectionService."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, test_macro_service: MacroIntrospectionService):
        """Test protection against SQL injection attempts."""
        malicious_inputs = [
            "'; DROP TABLE employees; --",
            "' OR '1'='1",
            "'; DELETE FROM employees; --",
            "UNION SELECT * FROM employees",
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(Exception):
                await test_macro_service.execute_macro("greet", {"name": malicious_input})
    
    @pytest.mark.asyncio
    async def test_large_result_handling(self, test_macro_service: MacroIntrospectionService):
        """Test handling of large result sets."""
        # This test depends on having a macro that could return large results
        # For now, we'll test with our existing data
        result = await test_macro_service.execute_macro("employees_by_department", {"dept": "Engineering"})
        
        # Should handle results correctly regardless of size
        assert isinstance(result, list)
        assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, test_macro_service: MacroIntrospectionService):
        """Test handling of query timeouts."""
        # This is a basic test - in a real scenario, you'd create a macro that takes a long time
        # For now, we'll just ensure normal execution works within reasonable time
        import time
        
        start_time = time.time()
        result = await test_macro_service.execute_macro("employee_count", {})
        end_time = time.time()
        
        # Should execute quickly
        assert (end_time - start_time) < 5.0  # 5 seconds should be more than enough
        assert len(result) == 1
