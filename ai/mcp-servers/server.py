from fastmcp import FastMCP
import mysql.connector
import os

# Create an MCP server using FastMCP
mcp = FastMCP("Product Database Server")

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_AMT_DB_HOST"),
        database=os.getenv("MYSQL_AMT_DB_NAME"),
        user=os.getenv("MYSQL_AMT_DB_USER"),
        password=os.getenv("MYSQL_AMT_DB_PASSWORD"),
        port=3306
    )

# Tool to list all products
@mcp.tool()
def list_products():
    """Returns a list of all products in the database."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, product FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": row["id"], "product": row["product"]}
        for row in rows
    ]


if __name__ == "__main__":
    # Run the server using Streamable HTTP transport
    # The correct syntax for FastMCP by jlowin
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)