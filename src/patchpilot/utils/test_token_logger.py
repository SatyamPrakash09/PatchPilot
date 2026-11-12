"""Simple test for token logger functionality."""

from patchpilot.utils.token_logger import TokenLogger, TokenUsage, create_token_logger


def test_token_usage_addition():
    """Test that TokenUsage can be added together."""
    usage1 = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
    usage2 = TokenUsage(input_tokens=200, output_tokens=100, total_tokens=300)

    combined = usage1 + usage2
    assert combined.input_tokens == 300
    assert combined.output_tokens == 150
    assert combined.total_tokens == 450
    print("✅ TokenUsage addition works correctly")


def test_token_usage_to_dict():
    """Test TokenUsage.to_dict() method."""
    usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
    result = usage.to_dict()

    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 50
    assert result["total_tokens"] == 150
    print("✅ TokenUsage.to_dict() works correctly")


def test_token_logger_silent_accumulation():
    """Test that token logger silently accumulates without per-call output."""
    logger = create_token_logger(verbose=True)

    # Reset to start fresh
    logger.reset_usage()

    # Simulate multiple LLM calls
    for i in range(3):
        mock_response = type('MockResponse', (), {
            'llm_output': {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}},
            'generations': []
        })()
        logger.on_llm_end(mock_response)

    # Check cumulative total
    usage = logger.get_total_usage()
    assert usage.input_tokens == 300
    assert usage.output_tokens == 150
    assert usage.total_tokens == 450
    print("✅ TokenLogger silently accumulates correctly")


def test_token_logger_reset():
    """Test that token logger can be reset."""
    logger = create_token_logger(verbose=False)

    # Add some tokens
    mock_response = type('MockResponse', (), {
        'llm_output': {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}},
        'generations': []
    })()
    logger.on_llm_end(mock_response)

    # Reset
    logger.reset_usage()
    usage = logger.get_total_usage()
    assert usage.input_tokens == 0
    assert usage.output_tokens == 0
    assert usage.total_tokens == 0
    print("✅ TokenLogger reset works correctly")


def test_token_logger_session_summary():
    """Test session summary display."""
    logger = create_token_logger(verbose=False)
    logger.reset_usage()

    # Simulate some usage
    logger.token_usage = TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500)

    # This should not raise an error
    logger.display_session_summary()

    print("✅ TokenLogger session summary works correctly")


if __name__ == "__main__":
    test_token_usage_addition()
    test_token_usage_to_dict()
    test_token_logger_silent_accumulation()
    test_token_logger_reset()
    test_token_logger_session_summary()
    print("\n✅ All tests passed!")