# MCP Integration Guide

This guide shows you how to connect the League Analysis MCP Server to various AI clients that support the Model Context Protocol.

## 🚀 Quick Start

1. **Install the package**: `uvx league-analysis-mcp-server` (or `pip install league-analysis-mcp-server`)
2. **Choose your client** from the options below
3. **Add configuration** to your client
4. **Restart your client**
5. **Test the connection**

The server will automatically guide you through Yahoo API setup on first run.

## 🔌 Client Configurations

### Claude Desktop

**Location:** 
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "league-analysis": {
      "command": "uvx",
      "args": ["league-analysis-mcp-server"]
    }
  }
}
```

### Claude Code

**Configuration:**
Add to your Claude Code MCP settings:
```json
{
  "mcpServers": {
    "league-analysis": {
      "command": "uvx",
      "args": ["league-analysis-mcp-server"]
    }
  }
}
```

### Continue.dev

**Location:** `~/.continue/config.json`

**Configuration:**
```json
{
  "mcpServers": [
    {
      "name": "league-analysis",
      "command": ["uvx", "league-analysis-mcp-server"]
    }
  ]
}
```

### Cline (VSCode Extension)

**Configuration:**
Add to your Cline settings:
```json
{
  "mcpServers": {
    "league-analysis": {
      "command": "uvx",
      "args": ["league-analysis-mcp-server"]
    }
  }
}
```

### Other MCP Clients

For any MCP-compatible client:
- **Command:** `uvx`
- **Arguments:** `["league-analysis-mcp-server"]`
- **Transport:** stdio (default)
- **No working directory needed!**

## 📁 Configuration Examples

Pre-filled configuration files are available in the `example_configs/` directory:

- `claude_desktop_config.json` - For Claude Desktop
- `claude_code_config.json` - For Claude Code  
- `continue_config.json` - For Continue.dev

**To use:**
1. Copy the appropriate file
2. Place in your client's configuration directory
3. No path modifications needed - uses PyPI package!

## 🧪 Testing Your Connection

### 1. Basic Connection Test

After configuring your client, ask:
```
"Can you get server info for the league analysis server?"
```

Expected response includes server name, supported sports, and authentication status.

### 2. Tool Testing

Test specific tools:
```
"List available seasons for NFL"
"What fantasy sports analysis tools are available?"
"Show me the current server configuration"
```

### 3. Resource Testing

Test resources:
```
"Show me a league overview for NFL league 123456"
"Get current week information for NBA league 789012"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Server Not Found
**Error:** MCP client cannot find the server

**Solutions:**
- Ensure UV is installed and accessible: `uv --version`
- Test server manually: `uvx league-analysis-mcp-server`
- Verify the package is installed: `pip show league-analysis-mcp-server`

#### 2. Authentication Required
**Error:** Yahoo API authentication missing

**Solutions:**
- The server will automatically guide you through setup on first run
- Create Yahoo Developer app at: https://developer.yahoo.com/apps/
- Follow the server's interactive setup instructions

#### 3. Permission Errors
**Error:** Client cannot execute commands

**Solutions:**
- Ensure client has permission to run UV
- On Windows, verify PowerShell execution policy
- Try running as administrator if needed

### Debug Steps

1. **Test server manually:**
   ```bash
   uvx league-analysis-mcp-server
   ```

2. **Check logs:**
   - Server logs appear in client's MCP logs
   - Look for initialization messages

3. **Verify installation:**
   ```bash
   pip show league-analysis-mcp-server
   ```

## 🔧 Advanced Configuration

### Alternative Commands

If UV is not in PATH:

```json
{
  "command": "/full/path/to/uv",
  "args": ["league-analysis-mcp-server"]
}
```

Or using pip installed version:

```json
{
  "command": "league-analysis-mcp-server"
}
```

## 🎯 Expected Functionality

Once connected, your AI client will have access to:

### Available Tools
- League information and standings
- Historical draft analysis
- Manager performance evaluation
- Trade likelihood predictions
- Season comparisons
- Advanced analytics

### Available Resources
- League overviews
- Current week summaries  
- Historical trends
- Manager profiles

### Supported Sports
- NFL (National Football League)
- NBA (National Basketball Association)
- MLB (Major League Baseball)
- NHL (National Hockey League)

## 📞 Support

If you encounter issues:

1. Check this troubleshooting guide
2. Test the server manually: `uvx league-analysis-mcp-server`
3. Review server logs in your MCP client
4. Ensure UV is installed and accessible

The server is designed to provide helpful error messages and automatic setup guidance.