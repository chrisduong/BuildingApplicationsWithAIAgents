#!/usr/bin/env python3
"""
MCP Math Server — exposes a single `math` tool that safely evaluates
arithmetic expressions. Communicates via the official MCP stdio transport.
"""
import ast
import asyncio
import operator

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def eval_expr(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_expr(node.left), eval_expr(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_expr(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def compute_math(expression: str) -> float:
    """Safely evaluate a simple arithmetic expression."""
    cleaned = "".join(ch for ch in expression if ch.isdigit() or ch in "+-*/()^ .")
    cleaned = cleaned.strip().replace("^", "**")
    if not cleaned:
        raise ValueError(f"No valid arithmetic expression found in: {expression!r}")
    tree = ast.parse(cleaned, mode="eval")
    return eval_expr(tree.body)


app = Server("math")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="math",
            description="Safely evaluate an arithmetic expression (supports +, -, *, /, **, parentheses).",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The arithmetic expression to evaluate, e.g. '(3 + 5) * 12'",
                    }
                },
                "required": ["expression"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "math":
        raise ValueError(f"Unknown tool: {name!r}")

    expression = arguments.get("expression", "")
    try:
        result = compute_math(expression)
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
