#!/usr/bin/env python3
import yaml
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path
import base64

class JiraFieldUpdater:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.base_url = self.config['jira']['url'].rstrip('/')
        
        # Setup Basic Auth
        auth_str = f"{self.config['jira']['email']}:{self.config['jira']['token']}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }
        
        # Setup logging with DEBUG level for file and INFO for console
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(message)s')  # Simplified console output
        
        # Create handlers
        file_handler = logging.FileHandler(
            log_dir / f'jira_update_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Verify authentication
        self._verify_authentication()

        # Get and store field metadata for all configured fields
        self.field_metadata = {}
        for field_name, field_config in self.config['fields'].items():
            field_id = field_config['id']
            metadata = self.get_field_metadata(field_id)
            if metadata:
                self.field_metadata[field_id] = metadata
                self.logger.debug(f"Field {field_name} ({field_id}) metadata: {metadata}")
            else:
                self.logger.warning(f"Could not fetch metadata for field {field_name} ({field_id})")

        self.project_types = {}
        self._cache_project_types()


    def _verify_authentication(self):
        """Verify that we can authenticate with Jira."""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                headers=self.headers
            )
            response.raise_for_status()
            user_info = response.json()
            self.logger.info(f"Successfully authenticated as {user_info.get('displayName', 'unknown user')}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            if response.status_code == 401:
                self.logger.error("Invalid credentials. Please check your email and API token.")
            elif response.status_code == 403:
                self.logger.error("You don't have sufficient permissions.")
            sys.exit(1)

    def _load_config(self, config_path: str) -> dict:
        """Load and validate the YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['jira.url', 'jira.email', 'jira.token', 'fields']
            for field in required_fields:
                keys = field.split('.')
                current = config
                for key in keys:
                    if key not in current:
                        raise ValueError(f"Missing required configuration: {field}")
                    current = current[key]
            
            return config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            sys.exit(1)

    def _cache_project_types(self):
        """Cache project types for all configured projects"""
        for field_config in self.config['fields'].values():
            for project_key in field_config['projects'].keys():
                if project_key not in self.project_types:
                    self.project_types[project_key] = self.get_project_type(project_key)

    def get_project_type(self, project_key: str) -> str:
        """Fetch project type from Jira"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{project_key}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            # Check projectTypeKey for next-gen vs company-managed
            project_type_key = data.get('projectTypeKey', '')
            if 'next-gen' in project_type_key.lower():
                return 'next-gen'
            elif 'software' in project_type_key.lower():
                return 'company-managed'
            return 'undetermined'
            
        except Exception as e:
            self.logger.warning(f"Could not determine project type for {project_key}: {str(e)}")
            return 'undetermined'

    def find_issues_without_field(self, project_key: str, field_id: str) -> List[dict]:
        """Find all issues in a project that don't have the specified field set."""
        issues = []
        start_at = 0
        batch_size = 100

        while True:
            try:
                jql = f'project = "{project_key}" AND cf[{field_id.replace("customfield_", "")}] is EMPTY'
                search_endpoint = f"{self.base_url}/rest/api/3/search"
                search_payload = {
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": batch_size,
                    "fields": ["id", "key", "issuetype"],
                }
                
                response = requests.post(
                    search_endpoint,
                    headers=self.headers,
                    json=search_payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Now storing both id and key
                batch_issues = [{
                    "id": issue['id'], 
                    "key": issue['key'],
                    "issue_type": issue['fields']['issuetype']['name'],
                } for issue in result['issues']]                
                issues.extend(batch_issues)
                
                if len(batch_issues) < batch_size:
                    break
                    
                start_at += batch_size
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error finding issues for {project_key}: {str(e)}")
                break
        
        return issues

    def check_field_screen_config(self, project_key: str, field_id: str):
        """Check if a field is on the edit screen for a project."""
        try:
            # Get all fields
            response = requests.get(
                f"{self.base_url}/rest/api/3/field",
                headers=self.headers
            )
            response.raise_for_status()
            fields = response.json()
            
            # Look for our field
            field = next((f for f in fields if f['id'] == field_id), None)
            if field:
                self.logger.info(f"Found field {field_id} ({field.get('name', 'Unknown')})")
                return True
                
            self.logger.warning(f"Field {field_id} not found in available fields")
            return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get field config for project {project_key}: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"Response content: {e.response.text}")
            return None

    def get_field_options(self, field_id: str) -> dict:
        """Get available options for a select field."""
        try:
            field_num = field_id.replace('customfield_', '')
            response = requests.get(
                f"{self.base_url}/rest/api/3/customField/{field_num}/option",
                headers=self.headers
            )
            response.raise_for_status()
            options = response.json()
            self.logger.debug(f"Available options: {options}")  # Changed to debug
            return options
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get field options: {str(e)}")
            return None

    def update_issue_field(self, issue_id: str, field_id: str, value: str) -> bool:
        try:
            options_response = self.get_field_options(field_id)
            if not options_response:
                return False
                    
            option = next((opt for opt in options_response['values'] if opt['value'] == value), None)
            if not option:
                self.logger.error(f"Value '{value}' not found in available options")
                return False

            endpoint = f"{self.base_url}/rest/api/3/issue/{issue_id}"
            payload = {
                "fields": {
                    field_id: {
                        "id": str(option['id']),  # API expects string ID
                        "value": option['value']
                    }
                }
            }

            self.logger.debug(f"Update payload for issue {issue_id}: {payload}")
            
            response = requests.put(
                endpoint, 
                headers=self.headers, 
                json=payload
            )
            
            if response.status_code != 204:  # Jira returns 204 on successful update            
                self.logger.error(f"Failed to update issue {issue_id}: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return False
                    
            self.logger.debug(f"Successfully updated issue {issue_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update issue {issue_id}: {str(e)}")
            return False
        
        
    def get_field_metadata(self, field_id: str) -> dict:
        """Get metadata for a specific custom field."""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/field",  # Note: changed endpoint
                headers=self.headers
            )
            response.raise_for_status()
            fields = response.json()
            
            # Find our specific field
            field = next((f for f in fields if f['id'] == field_id), None)
            if field:
                self.logger.info(f"Field metadata: {field}")
            return field
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get field metadata: {str(e)}")
            return None
    
    def create_or_update_automation_rule(
        self, 
        project_key: str, 
        field_id: str, 
        value: str,
        field_name: str
    ) -> bool:
        """Create or update automation rule for setting field on new issues."""
        try:
            # First, check if rule already exists
            rules_endpoint = f"{self.base_url}/rest/api/3/automation/rules"
            response = requests.get(
                f"{rules_endpoint}?projectKey={project_key}",
                headers=self.headers
            )
            response.raise_for_status()
            rules = response.json()
            
            rule_name = f"Set {field_name} for {project_key}"
            existing_rule = next(
                (rule for rule in rules['values'] if rule['name'] == rule_name),
                None
            )
            
            payload = {
                "name": rule_name,
                "projectKey": project_key,
                "trigger": {
                    "component": "ISSUE_CREATED",
                    "conditions": [{
                        "operator": "AND",
                        "conditions": [{
                            "field": "project",
                            "operator": "EQUALS",
                            "value": project_key
                        }]
                    }]
                },
                "actions": [{
                    "component": "FIELD_UPDATE",
                    "parameters": {
                        "field": field_id,
                        "value": value
                    }
                }]
            }
            
            if existing_rule:
                # Update existing rule
                response = requests.put(
                    f"{rules_endpoint}/{existing_rule['id']}",
                    headers=self.headers,
                    json=payload
                )
            else:
                # Create new rule
                response = requests.post(
                    rules_endpoint,
                    headers=self.headers,
                    json=payload
                )
            
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to configure automation rule for {project_key}: {str(e)}")
            if response.status_code == 403:
                self.logger.error("Make sure you have automation permissions for this project")
            return False

    def process_all_fields(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Process all fields and projects defined in the configuration."""
        results = {}
        
        for field_name, field_config in self.config['fields'].items():
            self.logger.info(f"\nProcessing field: {field_name}")
            field_results = {}
            field_id = field_config['id']
            
            for project_key, value in field_config['projects'].items():
                # Add project type to logging
                project_type = self.project_types.get(project_key, 'undetermined')
                self.logger.info(f"\nProcessing project {project_key} (Type: {project_type})")
                
                project_results = {
                    'issues_found': 0,
                    'issues_updated': 0,
                    'automation_rule': False,
                    'project_type': project_type,
                    'failed_issues': [],  # Change to store tuples/dicts with (key, type)
                    'successful_issues': [],  # New field to track successes with type
                }

                # Check if field is on screens
                has_field = self.check_field_screen_config(project_key, field_id)
                if has_field is None:
                    self.logger.error(f"Failed to check screen configuration for {project_key}")
                    project_results['error'] = 'Failed to check screen configuration'
                    field_results[project_key] = project_results
                    continue
                elif not has_field:
                    self.logger.error(f"Field {field_name} not found in screens for {project_key}")
                    project_results['error'] = 'Field not configured in project screens'
                    field_results[project_key] = project_results
                    continue                
                
                # Find and update issues
                issues = self.find_issues_without_field(project_key, field_id)
                project_results['issues_found'] = len(issues)
                
                self.logger.info(f"Found {len(issues)} issues to update")
                
                for issue in issues:
                    if self.update_issue_field(issue['id'], field_id, value):
                        project_results['issues_updated'] += 1
                        project_results['successful_issues'].append({
                            'key': issue['key'],
                            'type': issue['issue_type']
                        })
                    else:
                        project_results['failed_issues'].append({
                            'key': issue['key'],
                            'type': issue['issue_type']
                        })
                         
                if project_results['failed_issues']:
                    # Sort failed issues by key
                    sorted_failed = sorted(project_results['failed_issues'], key=lambda x: x['key'])
                    
                    # Convert the sorted list to a formatted string
                    failed_issues_str = ', '.join([
                        f"{issue['key']}({issue['type']})" 
                        for issue in sorted_failed
                    ])
                    
                    self.logger.warning(
                        f"\nFailed to update {len(project_results['failed_issues'])} issues in {project_key}:"
                        f"\nFailed issues: {failed_issues_str}"
                    )

                # Create/update automation rule
                project_results['automation_rule'] = self.create_or_update_automation_rule(
                    project_key,
                    field_id,
                    value,
                    field_name
                )
                
                field_results[project_key] = project_results
                
                self.logger.info(
                    f"Project {project_key} completed:"
                    f"\n  - Issues updated: {project_results['issues_updated']}/{project_results['issues_found']}"

                    f"issues updated, automation rule: "
                    f"{'created' if project_results['automation_rule'] else 'failed'}"

                )
            
            results[field_name] = field_results
        
        return results

def main():
    if len(sys.argv) != 2:
        print("Usage: jira-defaults config/defaults.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    updater = JiraFieldUpdater(config_path)
    results = updater.process_all_fields()
    
    print("\nUpdate Summary:")
    print("=" * 50)
    for field_name, field_results in results.items():
        print(f"\nField: {field_name}")
        for project, stats in field_results.items():
            print(f"\n  Project: {project} ({stats['project_type']})")
            print(f"  Issues found without value: {stats['issues_found']}")
            print(f"  Issues successfully updated: {stats['issues_updated']}")
            print(f"  Automation rule: {'✓' if stats['automation_rule'] else '✗'}")

    print("\nCheck the log file for detailed information.")

if __name__ == "__main__":
    main()
