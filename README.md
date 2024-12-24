# jira-field-sync

<div align="center">
  <img src="assets/logo-nobg.png" alt="jira-field-sync logo" width="200"/>
</div>

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
pip install jira-field-sync
```

Or from source:

```bash
git clone https://github.com/ergut/jira-field-sync
cd jira-field-sync
pip install -e .
```

## Finding Field IDs

Before configuring the tool, you'll need to find the IDs of your custom fields in Jira. Here's how:

1. Go to Jira Settings > Issues
2. Click on "Custom fields"
   - Direct URL: `https://your-domain.atlassian.net/secure/admin/ViewCustomFields.jspa`
3. Search for your field (e.g. "LOB")
4. Click on it and then click "Edit details"
5. In the URL or on the page, you'll see the ID number (e.g. `11196`)
6. The field ID to use in configuration is `customfield_` followed by this number (e.g. `customfield_11196`)

Note: You need admin access to view custom field settings.

## Configuration

Create a `defaults.yaml` file in your preferred location:

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
- The Jira custom field ID (found using steps above)
- A mapping of project keys to their default values

## Usage

Basic usage (provide the full path to your config file):

```bash
jira-field-sync /path/to/your/defaults.yaml
```

Check what would change without making updates:

```bash
jira-field-sync /path/to/your/defaults.yaml --dry-run
```

View current status:

```bash
jira-field-sync /path/to/your/defaults.yaml --status
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

## Sponsorship

This project is proudly sponsored by:

<div align="center">
  <a href="https://www.oredata.com">
    <img src="assets/oredata-logo-nobg.png" alt="OREDATA" width="300"/>
  </a>
</div>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
