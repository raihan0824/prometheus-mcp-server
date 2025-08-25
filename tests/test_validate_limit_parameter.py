"""
Comprehensive tests for the validate_limit_parameter helper function.
"""

import pytest
from prometheus_mcp_server.server import validate_limit_parameter


class TestValidateLimitParameter:
    """Test the validate_limit_parameter helper function."""

    def test_none_input(self):
        """Test that None input returns None."""
        result = validate_limit_parameter(None)
        assert result is None

    def test_integer_input(self):
        """Test that integer inputs are returned unchanged."""
        test_cases = [0, 1, 10, 100, 999999, -1]
        
        for value in test_cases:
            result = validate_limit_parameter(value)
            assert result == value
            assert isinstance(result, int)

    def test_valid_string_conversion(self):
        """Test that valid string integers are converted correctly."""
        test_cases = [
            ("0", 0),
            ("1", 1),
            ("10", 10),
            ("100", 100),
            ("999999", 999999),
            ("-1", -1),
            ("  20  ", 20),  # with whitespace
        ]
        
        for string_value, expected_int in test_cases:
            result = validate_limit_parameter(string_value)
            assert result == expected_int
            assert isinstance(result, int)

    def test_invalid_string_raises_error(self):
        """Test that invalid string values raise ValueError."""
        invalid_strings = [
            "invalid",
            "not_a_number", 
            "12.5",  # float string
            "1.0",   # float string
            "",      # empty string
            "  ",    # whitespace only
            "abc123",
            "123abc",
            "12 34", # space in middle
            "NaN",
            "infinity",
            "null",
        ]
        
        for invalid_value in invalid_strings:
            with pytest.raises(ValueError) as exc_info:
                validate_limit_parameter(invalid_value)
            
            # Verify error message format
            error_msg = str(exc_info.value)
            assert f"Invalid limit value '{invalid_value}'" in error_msg
            assert "must be a valid integer" in error_msg

    def test_edge_case_large_numbers(self):
        """Test very large numbers."""
        large_number = 999999999999
        
        # Test integer
        result = validate_limit_parameter(large_number)
        assert result == large_number
        
        # Test string conversion
        result = validate_limit_parameter(str(large_number))
        assert result == large_number

    def test_zero_values(self):
        """Test zero in different formats."""
        zero_cases = [0, "0", "-0", "+0"]
        
        for zero_value in zero_cases:
            result = validate_limit_parameter(zero_value)
            assert result == 0
            assert isinstance(result, int)

    def test_negative_numbers(self):
        """Test negative numbers in different formats."""
        negative_cases = [
            (-1, -1),
            (-100, -100),
            ("-1", -1),
            ("-100", -100),
        ]
        
        for input_value, expected in negative_cases:
            result = validate_limit_parameter(input_value)
            assert result == expected
            assert isinstance(result, int)

    def test_return_type_consistency(self):
        """Test that return types are consistent."""
        # None input should return None
        assert validate_limit_parameter(None) is None
        
        # All valid inputs should return int or None
        test_inputs = [0, 1, "0", "1", "100", -1, "-1"]
        
        for input_val in test_inputs:
            result = validate_limit_parameter(input_val)
            assert isinstance(result, int)

    def test_function_is_pure(self):
        """Test that function doesn't modify input and has no side effects."""
        original_value = "123"
        result = validate_limit_parameter(original_value)
        
        # Original value should be unchanged
        assert original_value == "123"
        assert result == 123
        
        # Multiple calls with same input should return same result
        result2 = validate_limit_parameter(original_value)
        assert result == result2

    def test_docstring_examples(self):
        """Test examples that might be in docstring."""
        # Common usage patterns
        assert validate_limit_parameter("20") == 20
        assert validate_limit_parameter(20) == 20
        assert validate_limit_parameter(None) is None
        
        with pytest.raises(ValueError):
            validate_limit_parameter("invalid")


class TestValidateLimitParameterIntegration:
    """Integration tests showing how the function works with MCP tools."""

    def test_typical_mcp_usage_patterns(self):
        """Test patterns commonly seen in MCP tool calls."""
        # Simulate what MCP clients might send
        mcp_client_inputs = [
            ("20", 20),      # String from JSON
            (20, 20),        # Direct integer
            (None, None),    # No limit provided
            ("0", 0),        # Zero limit
            ("1", 1),        # Single item limit
        ]
        
        for input_val, expected in mcp_client_inputs:
            result = validate_limit_parameter(input_val)
            assert result == expected

    def test_error_handling_for_user_feedback(self):
        """Test that error messages are user-friendly."""
        try:
            validate_limit_parameter("not_a_number")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            # Error should be descriptive for debugging
            assert "Invalid limit value 'not_a_number'" in error_msg
            assert "must be a valid integer" in error_msg