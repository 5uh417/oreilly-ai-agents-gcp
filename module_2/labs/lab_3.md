# Lab #3: Building API-Powered Agents with OpenAPI Tools

Welcome to the third lab of Module 2! You've learned to work with different models and combine various tool types. Now, you'll discover how to automatically generate tools from OpenAPI specifications, enabling your agents to interact with any REST API that follows the OpenAPI standard.

OpenAPI (formerly Swagger) is the industry standard for describing REST APIs. ADK's OpenAPI toolset can automatically parse these specifications and generate function tools for your agent, turning any well-documented API into an instant agent capability. This means you can integrate with thousands of existing APIs without writing custom integration code.

### **What You'll Learn**

- How to use ADK's `OpenAPIToolset` to automatically generate tools from API specifications.
- How to create and structure OpenAPI specifications for mock testing.
- How to configure agents to interact with REST APIs through generated tools.
- Best practices for working with external APIs in agent workflows.
- How to handle API responses and provide meaningful feedback to users.
- How to use httpbin.org as a testing platform for API interactions.

### **What You'll Need**

- A computer with Python 3.10 or higher installed.
- A code editor like Visual Studio Code.
- Access to the internet (for testing with httpbin.org).
- A Google account with access to Google AI Studio.
- Basic understanding of REST APIs and HTTP methods.

Let's dive into the world of API-powered agents.

## 1. Set Up Your OpenAPI Laboratory

Let's create a dedicated environment for experimenting with OpenAPI tools and external API integrations.

1. Open your terminal and create a new directory for this lab:

    ```console
    mkdir adk-openapi-lab
    cd adk-openapi-lab
    ```

2. Create and activate a Python virtual environment:

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    # On Windows: .venv\Scripts\activate
    ```

3. Install the required dependencies:

    ```console
    pip install google-adk
    ```

4. Create the project structure:

    ```console
    mkdir petstore_agent
    touch petstore_agent/__init__.py
    touch .env
    ```

5. Add the required import to the `__init__.py` file:

    ```python
    # petstore_agent/__init__.py
    from . import agent
    ```

6. Set up your environment variables in `.env`:

    ```
    GOOGLE_GENAI_USE_VERTEXAI=0
    GOOGLE_API_KEY=your-google-ai-studio-api-key-here
    ```

## 2. Understanding OpenAPI and Tool Generation

Before we build our agent, let's understand what makes OpenAPI toolsets so powerful:

### **What is OpenAPI?**

OpenAPI is a specification for describing REST APIs. It defines:
- **Endpoints**: What URLs and HTTP methods are available
- **Parameters**: What inputs each endpoint expects
- **Responses**: What data structure each endpoint returns
- **Authentication**: How to authenticate with the API
- **Data Models**: The structure of request and response objects

### **How ADK Generates Tools**

ADK's `OpenAPIToolset` performs the following magic:
1. **Parses** the OpenAPI specification (JSON or YAML)
2. **Generates** individual tools for each API endpoint
3. **Creates** proper function signatures with type hints
4. **Handles** HTTP requests, authentication, and error handling
5. **Returns** structured responses your agent can understand

This means a single OpenAPI spec can instantly give your agent dozens of capabilities!

## 3. Create Your Pet Store API Agent

Let's build an agent that can manage a pet store using a mock API. We'll use httpbin.org, which provides testing endpoints that echo back our requests.

### **Create the Agent Implementation**

Create `petstore_agent/agent.py` with the following code:

```python
import asyncio
import uuid  # For unique session IDs
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- OpenAPI Tool Imports ---
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

# --- Load Environment Variables ---
load_dotenv()

# --- Constants ---
AGENT_NAME_OPENAPI = "petstore_manager_agent"
GEMINI_MODEL = "gemini-2.0-flash"

# --- Sample OpenAPI Specification (JSON String) ---
# A basic Pet Store API example using httpbin.org as a mock server
openapi_spec_string = """
{
  "openapi": "3.0.0",
  "info": {
    "title": "Simple Pet Store API (Mock)",
    "version": "1.0.1",
    "description": "An API to manage pets in a store, using httpbin for responses."
  },
  "servers": [
    {
      "url": "https://httpbin.org",
      "description": "Mock server (httpbin.org)"
    }
  ],
  "paths": {
    "/get": {
      "get": {
        "summary": "List all pets (Simulated)",
        "operationId": "listPets",
        "description": "Simulates returning a list of pets. Uses httpbin's /get endpoint which echoes query parameters.",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "description": "Maximum number of pets to return",
            "required": false,
            "schema": { "type": "integer", "format": "int32" }
          },
          {
             "name": "status",
             "in": "query",
             "description": "Filter pets by status",
             "required": false,
             "schema": { "type": "string", "enum": ["available", "pending", "sold"] }
          }
        ],
        "responses": {
          "200": {
            "description": "A list of pets (echoed query params).",
            "content": { "application/json": { "schema": { "type": "object" } } }
          }
        }
      }
    },
    "/post": {
      "post": {
        "summary": "Create a pet (Simulated)",
        "operationId": "createPet",
        "description": "Simulates adding a new pet. Uses httpbin's /post endpoint which echoes the request body.",
        "requestBody": {
          "description": "Pet object to add",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                  "name": {"type": "string", "description": "Name of the pet"},
                  "tag": {"type": "string", "description": "Optional tag for the pet"}
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Pet created successfully (echoed request body).",
            "content": { "application/json": { "schema": { "type": "object" } } }
          }
        }
      }
    },
    "/get?petId={petId}": {
      "get": {
        "summary": "Info for a specific pet (Simulated)",
        "operationId": "showPetById",
        "description": "Simulates returning info for a pet ID. Uses httpbin's /get endpoint.",
        "parameters": [
          {
            "name": "petId",
            "in": "path",
            "description": "This is actually passed as a query param to httpbin /get",
            "required": true,
            "schema": { "type": "integer", "format": "int64" }
          }
        ],
        "responses": {
          "200": {
            "description": "Information about the pet (echoed query params)",
            "content": { "application/json": { "schema": { "type": "object" } } }
          },
          "404": { "description": "Pet not found (simulated)" }
        }
      }
    }
  }
}
"""

# --- Create OpenAPIToolset ---
petstore_toolset = OpenAPIToolset(
    spec_str=openapi_spec_string,
    spec_str_type='json',
    # No authentication needed for httpbin.org
    # Optional: tool_filter=['createPet', 'showPetById'] to limit available tools
)

# --- Agent Definition ---
root_agent = LlmAgent(
    name=AGENT_NAME_OPENAPI,
    model=GEMINI_MODEL,
    tools=[petstore_toolset],
    instruction="""You are a Pet Store assistant managing pets via an API.
    Use the available tools to fulfill user requests.

    Available operations:
    - listPets: Get a list of all pets (with optional filters)
    - createPet: Add a new pet to the store
    - showPetById: Get information about a specific pet

    When creating a pet, confirm the details echoed back by the API.
    When listing pets, mention any filters used (like limit or status).
    When showing a pet by ID, state the ID you requested.
    Always be helpful and explain what actions you're taking.
    """,
    description="Manages a Pet Store using tools generated from an OpenAPI spec."
)
```

### **Understanding the OpenAPI Specification**

Let's break down the key components of our OpenAPI spec:

- **`info`**: Metadata about the API
- **`servers`**: Base URLs where the API is hosted
- **`paths`**: Available endpoints and their operations
- **`operationId`**: Unique identifiers that become tool function names
- **`parameters`**: Input parameters for each endpoint
- **`requestBody`**: Structure for POST/PUT request bodies
- **`responses`**: Expected response formats

### **Understanding the Tool Generation**

When ADK processes this specification, it creates:
- `listPets()` function from the GET /get endpoint
- `createPet()` function from the POST /post endpoint
- `showPetById()` function from the GET /get?petId={petId} endpoint

Each function includes proper type hints, documentation, and error handling.

## 4. Test Your OpenAPI-Powered Agent

Let's see your automatically generated API tools in action!

### **Start the Agent**

1. From your project root directory, start the ADK web interface:

    ```console
    adk web
    ```

2. Open your browser to `http://127.0.0.1:8080` and test with these prompts:

    - `List all pets in the store`
    - `Show me pets with status 'available' and limit to 5 results`
    - `Create a new pet named 'Buddy' with tag 'friendly'`
    - `Show me information about pet ID 123`

### **Understanding the Responses**

Since we're using httpbin.org as a mock server, you'll see responses like:

```json
{
  "args": {"limit": "5", "status": "available"},
  "headers": {...},
  "url": "https://httpbin.org/get?limit=5&status=available"
}
```

This demonstrates that:
- Parameters are correctly passed to the API
- HTTP requests are properly formatted
- The agent can interpret and explain the responses

## 5. Advanced OpenAPI Features

### **Adding Authentication**

For real APIs that require authentication, you can add auth schemes:

```python
from google.adk.tools.openapi_tool.auth_schemes import APIKey
from google.adk.tools.openapi_tool.auth_credentials import AuthCredential

# Example: API Key authentication
auth_scheme = APIKey(name="X-API-Key", location="header")
auth_credential = AuthCredential(
    auth_type="API_KEY",
    value="your-api-key-here"
)

petstore_toolset = OpenAPIToolset(
    spec_str=openapi_spec_string,
    spec_str_type='json',
    auth_scheme=auth_scheme,
    auth_credential=auth_credential
)
```

### **Filtering Available Tools**

You can limit which tools are generated:

```python
petstore_toolset = OpenAPIToolset(
    spec_str=openapi_spec_string,
    spec_str_type='json',
    tool_filter=['createPet', 'listPets']  # Only generate these tools
)
```

### **Loading from External Files**

For real projects, load specifications from files:

```python
# Load from local file
with open('petstore-api.json', 'r') as f:
    spec_content = f.read()

# Or load from URL
import requests
response = requests.get('https://api.example.com/openapi.json')
spec_content = response.text

petstore_toolset = OpenAPIToolset(
    spec_str=spec_content,
    spec_str_type='json'
)
```

## 6. Real-World Integration Patterns

### **Error Handling and Validation**

```python
instruction="""You are a Pet Store assistant managing pets via an API.

Error Handling Guidelines:
- If an API call fails, explain the error clearly to the user
- For validation errors, guide the user on correct input format
- If a pet is not found, suggest alternative actions
- Always retry failed requests once before giving up

When APIs return errors, interpret them helpfully for the user.
"""
```

### **Response Interpretation**

```python
instruction="""You are a Pet Store assistant managing pets via an API.

Response Interpretation:
- When listing pets, summarize the key information clearly
- For creation operations, confirm success and provide next steps
- When showing pet details, highlight the most important information
- Always explain what the API response means in plain language

Transform technical API responses into user-friendly information.
"""
```

## 7. Best Practices for OpenAPI Tools

### **API Design Considerations**

- **Clear operationIds**: Use descriptive names like `getUserProfile` instead of `get1`
- **Detailed descriptions**: Provide context for what each endpoint does
- **Proper parameter types**: Use appropriate data types and validation
- **Meaningful examples**: Include example values in your spec

### **Agent Instructions**

- **Explain capabilities**: Tell users what operations are available
- **Guide usage**: Provide examples of how to request different actions
- **Handle failures**: Include guidance for when APIs are unavailable
- **Interpret responses**: Help users understand technical API responses

### **Security and Rate Limiting**

- **Authentication**: Always use secure authentication methods
- **Rate limiting**: Respect API rate limits in your instructions
- **Error handling**: Gracefully handle authentication failures
- **Logging**: Monitor API usage for debugging and optimization

## 8. Congratulations!

You've successfully built an agent powered by automatically generated OpenAPI tools!

In this lab, you learned to:

✅ **Generate tools automatically** from OpenAPI specifications

✅ **Configure API interactions** with proper parameters and requests

✅ **Handle API responses** and provide meaningful user feedback

✅ **Structure OpenAPI specs** for effective tool generation

✅ **Test API integrations** using mock services

✅ **Apply best practices** for production API integration

### **Key Takeaways**

- **Automation**: OpenAPI toolsets eliminate manual API integration work
- **Standardization**: Following OpenAPI standards ensures compatibility
- **Flexibility**: Generated tools work with any properly documented REST API
- **Testing**: Mock services like httpbin.org enable safe development and testing

### **What's Next?**

Now that you understand OpenAPI integration, you're ready to explore:
- **Production APIs**: Integrating with real business services
- **Authentication flows**: Handling OAuth, API keys, and other auth methods
- **Error handling**: Building robust error recovery mechanisms
- **Performance optimization**: Caching, batching, and rate limiting strategies

### **Frequently Asked Questions**

- **Can I use any OpenAPI specification?**
  Yes! ADK supports OpenAPI 3.0 specifications. Most modern APIs provide these specs.

- **How do I handle APIs that require complex authentication?**
  ADK supports OAuth2, API keys, and other standard auth methods. Check the authentication documentation for details.

- **What happens if an API endpoint changes?**
  Update your OpenAPI specification and regenerate the toolset. ADK will automatically adapt to the changes.

- **Can I customize the generated tool behavior?**
  You can filter which tools are generated and customize the agent's instructions for using them, but the core HTTP handling is automated.

- **How do I handle API rate limits?**
  Include rate limiting guidance in your agent instructions, and consider implementing retry logic with exponential backoff for production use.