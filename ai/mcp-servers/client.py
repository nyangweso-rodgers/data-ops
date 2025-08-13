import streamlit as st
import asyncio
import httpx
import json

# Streamlit app
st.title("MCP Product Database Query Tool")

# Tool selection - only list_products for basic testing
tool = st.selectbox("Select a tool", ["list_products"])

# Function to call MCP server via HTTP
async def call_mcp_tool_http(tool_name: str, arguments: dict = None):
    """Call MCP server tool via direct HTTP to the Streamable HTTP endpoint"""
    server_url = "http://mcp-server:8000/mcp"  # Using the working endpoint
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # Step 1: Initialize MCP session
            st.write("Initializing MCP session...")
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "roots": {},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "streamlit-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            init_response = await client.post(
                server_url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10.0
            )
            
            st.write(f"Initialize response: {init_response.status_code}")
            if init_response.status_code != 200:
                st.error(f"Initialize failed: {init_response.text}")
                return None
                
            init_result = init_response.json()
            st.write(f"Initialize result: {init_result}")
            
            # Extract session ID if present
            session_id = None
            if "result" in init_result and "sessionId" in init_result["result"]:
                session_id = init_result["result"]["sessionId"]
                st.write(f"Session ID: {session_id}")
            
            # Step 2: Send initialized notification (required by MCP protocol)
            st.write("Sending initialized notification...")
            initialized_request = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            if session_id:
                headers["Mcp-Session-Id"] = session_id
            
            await client.post(
                server_url,
                json=initialized_request,
                headers=headers,
                timeout=10.0
            )
            
            # Step 3: Call the actual tool
            st.write(f"Calling tool: {tool_name}")
            tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }
            
            if session_id:
                headers["Mcp-Session-Id"] = session_id
            
            tool_response = await client.post(
                server_url,
                json=tool_request,
                headers=headers,
                timeout=30.0
            )
            
            st.write(f"Tool response status: {tool_response.status_code}")
            tool_response.raise_for_status()
            
            result = tool_response.json()
            st.success("Tool call successful!")
            
            # Handle MCP response format
            if "result" in result:
                return result["result"]
            elif "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            else:
                return result
                
        except httpx.HTTPStatusError as e:
            st.error(f"HTTP {e.response.status_code}: {e.response.text}")
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
            raise Exception(f"Request failed: {e}")

# Button to execute query
if st.button("Run Query"):
    try:
        # Run the async function - only list_products
        result = asyncio.run(call_mcp_tool_http(tool, {}))
        
        # Display results
        st.subheader("Results")
        
        # Handle the response
        if isinstance(result, dict) and "content" in result:
            # MCP tool response format
            content = result["content"]
            if isinstance(content, list) and content:
                # Extract text content
                text_content = content[0].get("text", str(content[0]))
                try:
                    # Try to parse as JSON
                    parsed_data = json.loads(text_content)
                    if isinstance(parsed_data, list):
                        st.table(parsed_data)
                    else:
                        st.json(parsed_data)
                except (json.JSONDecodeError, ValueError):
                    st.write(text_content)
            else:
                st.write("No content in response")
        elif isinstance(result, list):
            if result:
                st.table(result)
            else:
                st.write("No results found.")
        elif isinstance(result, dict):
            if result:
                st.json(result)
            else:
                st.write("No results found.")
        else:
            st.write(str(result))
                
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.write("Make sure the MCP server is running and accessible.")

# Debug section - show connection test
with st.expander("Debug Info"):
    if st.button("Test Connection to mcp_server"):
        try:
            async def test_connection():
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://mcp_server:8000/", timeout=10.0)
                    return f"Status: {response.status_code}, Response: {response.text[:200]}..."
            
            test_result = asyncio.run(test_connection())
            st.success(f"Connection test result: {test_result}")
        except Exception as e:
            st.error(f"Connection test failed: {e}")
    
    if st.button("Test Connection to localhost"):
        try:
            async def test_localhost():
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/", timeout=10.0)
                    return f"Status: {response.status_code}, Response: {response.text[:200]}..."
            
            test_result = asyncio.run(test_localhost())
            st.success(f"Localhost test result: {test_result}")
        except Exception as e:
            st.error(f"Localhost test failed: {e}")
    
    if st.button("Test GET request to server"):
        try:
            async def test_get_request():
                urls_to_test = [
                    "http://mcp-server:8000",
                    "http://mcp-server:8000/mcp",
                    "http://mcp-server:8000/mcp/",
                    "http://172.18.0.2:8000",
                    "http://172.18.0.2:8000/mcp"
                ]
                
                results = []
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    for url in urls_to_test:
                        try:
                            response = await client.get(url, timeout=5.0)
                            results.append(f"✅ {url} -> {response.status_code}: {response.text[:100]}...")
                        except Exception as e:
                            results.append(f"❌ {url} -> Error: {str(e)}")
                
                return results
            
            test_results = asyncio.run(test_get_request())
            for result in test_results:
                st.write(result)
                
        except Exception as e:
            st.error(f"GET test failed: {e}")
    
    # Show network debug info
    st.write("**Network Debug Info:**")
    import socket
    try:
        hostname = socket.gethostname()
        st.write(f"Client hostname: {hostname}")
        
        # Try to resolve mcp_server
        try:
            server_ip = socket.gethostbyname("mcp_server")
            st.write(f"mcp_server resolves to: {server_ip}")
        except socket.gaierror as e:
            st.error(f"Cannot resolve mcp_server: {e}")
            
    except Exception as e:
        st.error(f"Network info error: {e}")

# Instructions
st.markdown("""
### Instructions
1. Click "Run Query" to list all products from the database.

### Technical Details
- This client makes direct HTTP requests to the FastMCP Streamable HTTP endpoint
- Uses MCP JSON-RPC protocol format
- Server endpoint: `http://mcp_server:8000/mcp`
- Testing only the `list_products` tool

### Troubleshooting
If you get connection errors:
1. Ensure the MCP server container is running
2. Check that both containers are on the same Docker network
3. Verify the server is listening on port 8000
4. Use the "Test Connection" button in the Debug Info section
""")