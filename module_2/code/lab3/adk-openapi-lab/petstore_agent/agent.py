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
