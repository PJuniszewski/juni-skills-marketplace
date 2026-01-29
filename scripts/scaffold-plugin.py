#!/usr/bin/env python3
"""
Generate plugin boilerplate for juni-skills-marketplace.

Usage:
    python scripts/scaffold-plugin.py --name my-plugin
    python scripts/scaffold-plugin.py --name my-plugin --tier community --with-hooks --with-agents
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_author() -> tuple[str, str]:
    """Get author name and email from git config."""
    try:
        name = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        name = "Your Name"

    try:
        email = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        email = "you@example.com"

    return name, email


def create_manifest(name: str, tier: str, author: str, with_hooks: bool, with_agents: bool) -> str:
    """Generate plugin.json content."""
    if tier == "curated":
        capabilities = '''{
      "network": {
        "mode": "none"
      }
    }'''
        risk = ""
    else:
        capabilities = '''{
      "network": {
        "mode": "allowlist",
        "domains": ["api.example.com"]
      }
    }'''
        risk = ''',
    "risk": {
      "dataEgress": "low",
      "notes": "Describe what data is sent and where"
    }'''

    return f'''{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "TODO: Brief description of {name}",
  "policyTier": "{tier}",
  "author": "{author}",
  "capabilities": {capabilities}{risk}
}}
'''


def create_example_command(name: str) -> str:
    """Generate example command markdown."""
    return f'''---
description: Example command for {name}
---

# Example Command

This is a sample command. Replace with your actual implementation.

## Usage

Run this command to see a greeting.

## Implementation

When invoked, respond with a friendly greeting that includes the plugin name "{name}".
'''


def create_example_skill(name: str) -> str:
    """Generate example skill markdown."""
    return f'''---
description: Example skill for {name}. Use when the user asks about {name} features.
---

# {name.replace("-", " ").title()} Skill

This skill provides guidance on using {name}.

## When to Use

- User asks "how do I use {name}?"
- User wants to learn about {name} features
- User needs help with {name} configuration

## Response Guidelines

Provide helpful information about {name}. Include:
1. Basic usage examples
2. Common configuration options
3. Troubleshooting tips
'''


def create_example_hook() -> str:
    """Generate example hook configuration."""
    return '''---
description: Example hook that logs tool usage
event: PostToolUse
---

# Post Tool Use Logger

This hook runs after any tool is used.

## Purpose

Log tool usage for debugging or monitoring purposes.

## Implementation

After a tool is used, output a brief log message:
"[Hook] Tool completed: {tool_name}"
'''


def create_example_agent(name: str) -> str:
    """Generate example agent markdown."""
    return f'''---
description: Specialist agent for {name} tasks
tools:
  - Read
  - Grep
  - Glob
---

# {name.replace("-", " ").title()} Agent

You are a specialist agent for {name} tasks.

## Your Role

- Analyze code related to {name}
- Provide recommendations
- Execute specific subtasks

## Guidelines

1. Be thorough but concise
2. Focus on the specific task at hand
3. Report findings clearly
'''


def create_readme(name: str, tier: str, author: str) -> str:
    """Generate README.md content."""
    tier_badge = "curated" if tier == "curated" else "community"
    network_section = ""
    if tier == "community":
        network_section = """
## Network Access

This plugin requires network access to:
- `api.example.com` - TODO: describe what this is used for

"""

    return f'''# {name}

> TODO: Brief description of what {name} does

![Tier](https://img.shields.io/badge/tier-{tier_badge}-{"blue" if tier == "curated" else "orange"})
![Version](https://img.shields.io/badge/version-1.0.0-green)

## Installation

```bash
claude /plugin install juni-skills:{name}
```

## Usage

```bash
# Run the example command
claude /example
```

## Commands

| Command | Description |
|---------|-------------|
| `/example` | TODO: describe this command |
{network_section}
## Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/{name}.git

# Test locally
claude --plugin-path ./{name}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

{author}
'''


def create_license(author: str) -> str:
    """Generate MIT LICENSE content."""
    year = datetime.now().year
    return f'''MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''


def create_github_workflow(name: str) -> str:
    """Generate GitHub Actions workflow for validation."""
    return f'''name: Validate Plugin

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Validate plugin structure
        run: |
          echo "Validating {name} plugin..."

          # Check required files
          test -f .claude-plugin/plugin.json || test -f plugin.json || {{ echo "Missing plugin.json"; exit 1; }}
          test -f README.md || {{ echo "Missing README.md"; exit 1; }}
          test -f LICENSE || {{ echo "Missing LICENSE"; exit 1; }}

          # Check for content directories
          has_content=false
          for dir in commands hooks agents skills; do
            if [ -d "$dir" ]; then
              has_content=true
              break
            fi
          done

          if [ "$has_content" = false ]; then
            echo "No content directories found (commands/, hooks/, agents/, or skills/)"
            exit 1
          fi

          echo "Plugin structure is valid!"
'''


def scaffold_plugin(
    name: str,
    tier: str,
    author: str,
    with_hooks: bool,
    with_agents: bool,
    output_dir: Path
) -> list[str]:
    """Create plugin directory structure and files."""
    created_files = []
    plugin_dir = output_dir / name

    if plugin_dir.exists():
        print(f"Error: Directory '{plugin_dir}' already exists")
        sys.exit(1)

    # Create directories
    dirs_to_create = [
        plugin_dir / ".claude-plugin",
        plugin_dir / "commands",
        plugin_dir / "skills" / "example",
        plugin_dir / ".github" / "workflows",
    ]

    if with_hooks:
        dirs_to_create.append(plugin_dir / "hooks")

    if with_agents:
        dirs_to_create.append(plugin_dir / "agents")

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    # Create files
    files = [
        (plugin_dir / ".claude-plugin" / "plugin.json", create_manifest(name, tier, author, with_hooks, with_agents)),
        (plugin_dir / "commands" / "example.md", create_example_command(name)),
        (plugin_dir / "skills" / "example" / "skill.md", create_example_skill(name)),
        (plugin_dir / "README.md", create_readme(name, tier, author)),
        (plugin_dir / "LICENSE", create_license(author)),
        (plugin_dir / ".github" / "workflows" / "validate.yml", create_github_workflow(name)),
    ]

    if with_hooks:
        files.append((plugin_dir / "hooks" / "post-tool-use.md", create_example_hook()))

    if with_agents:
        files.append((plugin_dir / "agents" / "specialist.md", create_example_agent(name)))

    for path, content in files:
        path.write_text(content, encoding="utf-8")
        created_files.append(str(path.relative_to(output_dir)))

    return created_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate plugin boilerplate for juni-skills-marketplace"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Plugin name (lowercase with hyphens, e.g., my-plugin)"
    )
    parser.add_argument(
        "--tier", "-t",
        choices=["curated", "community"],
        default="curated",
        help="Plugin tier (default: curated)"
    )
    parser.add_argument(
        "--author", "-a",
        help="Author name (default: from git config)"
    )
    parser.add_argument(
        "--with-hooks",
        action="store_true",
        help="Include hooks/ directory with example"
    )
    parser.add_argument(
        "--with-agents",
        action="store_true",
        help="Include agents/ directory with example"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path.cwd(),
        help="Output directory (default: current directory)"
    )

    args = parser.parse_args()

    # Validate plugin name
    import re
    if not re.match(r"^[a-z][a-z0-9-]*$", args.name):
        print(f"Error: Plugin name must be lowercase with hyphens (e.g., my-plugin)")
        sys.exit(1)

    # Get author
    if args.author:
        author = args.author
    else:
        git_name, _ = get_git_author()
        author = git_name

    print(f"Scaffolding plugin: {args.name}")
    print(f"  Tier: {args.tier}")
    print(f"  Author: {author}")
    print(f"  Hooks: {'yes' if args.with_hooks else 'no'}")
    print(f"  Agents: {'yes' if args.with_agents else 'no'}")
    print()

    created = scaffold_plugin(
        name=args.name,
        tier=args.tier,
        author=author,
        with_hooks=args.with_hooks,
        with_agents=args.with_agents,
        output_dir=args.output
    )

    print("Created files:")
    for f in sorted(created):
        print(f"  {f}")

    print()
    print("Next steps:")
    print(f"  1. cd {args.name}")
    print(f"  2. Edit .claude-plugin/plugin.json with your plugin details")
    print(f"  3. Replace commands/example.md with your commands")
    print(f"  4. Update README.md")
    print(f"  5. git init && git add -A && git commit -m 'Initial commit'")
    print(f"  6. Push to GitHub")
    print(f"  7. Submit PR to juni-skills-marketplace")

    if args.tier == "community":
        print()
        print("Community tier reminder:")
        print("  - Update capabilities.network.domains in plugin.json")
        print("  - Set accurate risk.dataEgress level")
        print("  - Document what data is sent to external services")


if __name__ == "__main__":
    main()
