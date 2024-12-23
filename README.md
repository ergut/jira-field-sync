# Jira Project Defaults

A tool for managing project-level custom field defaults in Jira. This tool allows you to:
- Set default values for custom fields across multiple projects
- Update existing issues that don't have values set
- Create automation rules for new issues

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/jira-project-defaults.git
cd jira-project-defaults

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install the package
pip install -e .
```

## Configuration

Create a YAML configuration file (e.g., `config/defaults.yaml`):

```yaml
# Jira instance configuration
jira:
  url: "https://your-domain.atlassian.net"
  token: "your-api-token"

# Field configurations
fields:
  lob:  # Line of Business field
    id: "customfield_11195"
    projects:
      ARGE: "R&D"
      SALES: "Sales"
      MKTG: "Marketing"
```

## Usage

```bash
# Using the installed command
jira-defaults config/defaults.yaml

# Or using Python directly
python -m jira_defaults.updater config/defaults.yaml
```

## Features

- **Multi-field Support**: Configure defaults for multiple custom fields
- **Project-specific Values**: Set different default values per project
- **Selective Updates**: Only updates issues that don't have values set
- **Automation Rules**: Creates or updates rules for new issues
- **Detailed Logging**: Comprehensive logging of all operations
- **Summary Reports**: Provides a clear summary of actions taken

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black src/
isort src/

# Check code style
flake8 src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
