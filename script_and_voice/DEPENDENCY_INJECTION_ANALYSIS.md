# Dependency Injection Benefits for Paraphraser Class

## Current Implementation Problems

```python
class Paraphraser:
    def __init__(self, config):
        # PROBLEM: Tight coupling to Anthropic API
        self.client = Anthropic(
            api_key=config["api"]["anthropic"]["api_key"],
            max_retries=config["api"]["anthropic"].get("max_retries", 1),
        )
        # PROBLEM: Class knows too much about config structure
        self.model = config["api"]["anthropic"]["model"]
        self.max_tokens = config["api"]["anthropic"].get("max_tokens", 4096)
```

**Issues:**
- ❌ **Hard to Test**: Cannot easily mock the API client
- ❌ **Inflexible**: Locked into Anthropic API
- ❌ **Violates Single Responsibility**: Manages both paraphrasing logic AND API client
- ❌ **Configuration Dependency**: Must know about API structure
- ❌ **No Interface Segregation**: Depends on concrete implementation

## Proposed Dependency Injection Solution

```python
class ParaphraserWithDI:
    def __init__(self, ai_client: AIClientInterface, config: dict):
        # ✅ BENEFIT: Depends on abstraction, not concrete implementation
        self.ai_client = ai_client
        self.config = config  # Only needs script-related config
    
    @classmethod
    def create_from_config(cls, config: dict) -> 'ParaphraserWithDI':
        # ✅ BENEFIT: Factory method handles client creation
        ai_client = create_ai_client(config)
        return cls(ai_client, config)
```

## Key Benefits

### 1. ✅ **Testability**
```python
# Easy to test with mock client
mock_client = MockAIClient(json_responses=[{"test": "response"}])
paraphraser = ParaphraserWithDI(mock_client, config)

# Test behavior without hitting real API
result = paraphraser.generate_outline("test input")
assert result == {"test": "response"}
```

### 2. ✅ **Flexibility - Multiple Providers**
```python
# Anthropic client
anthropic_client = AnthropicClient(api_key="...", model="claude-3-5-sonnet")
paraphraser_anthropic = ParaphraserWithDI(anthropic_client, config)

# OpenAI client (same Paraphraser class!)
openai_client = OpenAIClient(api_key="...", model="gpt-4")
paraphraser_openai = ParaphraserWithDI(openai_client, config)

# Mock for testing
mock_client = MockAIClient()
paraphraser_test = ParaphraserWithDI(mock_client, config)
```

### 3. ✅ **Separation of Concerns**
```python
class ParaphraserWithDI:
    # ONLY responsible for paraphrasing logic
    def generate_outline(self, text, language):
        messages = self.create_outline_prompt(text, language)
        return self.ai_client.generate_json_response(messages)  # Delegates to injected client

class AnthropicClient:
    # ONLY responsible for Anthropic API communication
    def generate_json_response(self, messages):
        # Handle Anthropic-specific API calls
```

### 4. ✅ **Configuration Independence**
```python
# Paraphraser only needs script-related config
paraphraser_config = {
    'script': {'total_words': 1000, 'paragraphs': 10},
    'paths': {'temp': '/tmp'}
}

# API configuration is handled elsewhere
ai_client = create_ai_client(full_config)
paraphraser = ParaphraserWithDI(ai_client, paraphraser_config)
```

### 5. ✅ **Easy Provider Switching**
```python
def create_paraphraser(provider: str, config: dict) -> ParaphraserWithDI:
    if provider == "anthropic":
        client = AnthropicClient(config['api']['anthropic']['api_key'])
    elif provider == "openai":
        client = OpenAIClient(config['api']['openai']['api_key'])
    elif provider == "mock":
        client = MockAIClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    return ParaphraserWithDI(client, config)

# Switch providers easily
paraphraser = create_paraphraser("anthropic", config)
# or
paraphraser = create_paraphraser("openai", config)
```

## Implementation Strategy

### Phase 1: Create Interface & Implementations
1. ✅ Create `AIClientInterface` (abstract base class)
2. ✅ Implement `AnthropicClient` 
3. ✅ Implement `OpenAIClient`
4. ✅ Implement `MockAIClient` for testing

### Phase 2: Refactor Paraphraser Class
1. Update constructor to accept `AIClientInterface`
2. Replace direct API calls with `self.ai_client.method_name()`
3. Add factory method for backward compatibility
4. Update configuration structure

### Phase 3: Update Other Classes
1. Apply same pattern to `BRollFinder`
2. Apply same pattern to `VectorMatcher`
3. Apply same pattern to `MetaExtractor`

## Code Quality Improvements

### SOLID Principles Compliance
- **S**ingle Responsibility: Each class has one clear purpose
- **O**pen/Closed: Easy to add new AI providers without modifying existing code
- **L**iskov Substitution: Any AIClientInterface implementation can be substituted
- **I**nterface Segregation: Clients depend only on interfaces they use
- **D**ependency Inversion: Depend on abstractions, not concrete implementations

### Testing Benefits
```python
def test_outline_generation():
    # Arrange
    mock_client = MockAIClient(json_responses=[expected_outline])
    paraphraser = ParaphraserWithDI(mock_client, config)
    
    # Act
    result = paraphraser.generate_outline("input text", "french")
    
    # Assert
    assert result == expected_outline
    assert mock_client.json_call_count == 1
```

## Conclusion

Dependency injection would significantly improve the codebase by:
- Making it more testable and maintainable
- Providing flexibility to switch between AI providers
- Following SOLID principles and best practices
- Reducing coupling between components
- Making the code more professional and enterprise-ready

The investment in refactoring would pay off through:
- Easier unit testing
- Better code organization
- Future-proofing for new AI providers
- Reduced technical debt
- More confident deployments