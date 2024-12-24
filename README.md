# Jira Project Defaults

A Python tool for managing project-level custom field defaults in Jira. Think of it as a "set it and forget it" solution for keeping your Jira fields consistent across projects.

## What Problem Does This Solve?

Managing custom field values across multiple Jira projects can be tedious and error-prone. This tool helps you:

- Set default values for custom fields at the project level
- Automatically update existing issues missing the correct values
- Create automation rules to maintain these defaults for new issues
- Monitor compliance across your projects

For example, you might want all issues in your R&D projects to have "R&D" as their Line of Business (LOB), while your Sales projects should have "Sales" as their LOB. Note that this tool only updates existing custom fields - it cannot create new ones. You'll need to create any custom fields through the Jira UI first.

## Prerequisites

Before you start:

1. **Jira Access**
   - An Atlassian account with admin or project admin permissions
   - An [API token](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Write access to the projects you want to manage

2. **Project Configuration**
   - The custom fields must be added to your project's screens
   - Field options (like "R&D", "Sales", etc.) must be pre-configured in Jira
   - Projects should be either company-managed or next-gen

3. **System Requirements**
   - Python 3.7 or higher
   - pip for package installation

## Installation

```bash
pip install jira-project-defaults
```

Or from source:

```bash
git clone https://github.com/yourusername/jira-project-defaults
cd jira-project-defaults
pip install -e .
```

## Configuration

Create a `defaults.yaml` file based on the template:

```yaml
# Jira instance configuration
jira:
  url: "https://your-domain.atlassian.net"
  email: "your.email@example.com"
  token: "your-api-token"
  
# Field configurations
fields:
  lob:  # Line of Business field
    id: "customfield_11196"
    projects:
      ARGE: "R&D"
      SALES: "Sales"
      MKTG: "Marketing"
```

Each field configuration needs:

- A descriptive name (e.g., "lob")
- The Jira custom field ID
- A mapping of project keys to their default values

## Usage

Basic usage:

```bash
jira-defaults config/defaults.yaml
```

Check what would change without making updates:

```bash
jira-defaults config/defaults.yaml --dry-run
```

View current status:

```bash
jira-defaults config/defaults.yaml --status
```

## How It Works

When you run the tool, it:

1. Validates your configuration against available field options
2. Finds issues missing the correct default values
3. Updates those issues to match project defaults
4. Generates detailed logs and reports

**Note:** While we initially planned to include automation rules for new issues, this feature isn't currently possible due to limitations in Jira's API. The Jira Cloud REST API doesn't provide endpoints for programmatically creating or managing automation rules.

## Logging

The tool creates detailed logs in the `logs` directory:

- Daily log files with timestamp: `jira_update_YYYYMMDD.log`
- Console output for quick status checks
- Detailed error reporting and success tracking

## Contributing

Contributions are welcome! Check out our [Roadmap](ROADMAP.md) for planned features and improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
