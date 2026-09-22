#!/usr/bin/env python3
"""
Agent Skills Generator
Automatically generates .github/skills directory structure from README.md

This script:
1. Parses README.md for skill entries matching: - **[provider/skill-name](url)** - description
2. Creates directory structure: .github/skills/[provider]/[skill-name]/
3. Generates SKILL.md file for each skill with metadata and formatting
4. Reports progress and statistics
"""

import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime


class SkillsGenerator:
    """Generates agent skill directory structure and SKILL.md files."""
    
    SKILL_PATTERN = r'^\s*-\s*\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*-\s*(.+)$'
    BASE_OUTPUT_DIR = '.github/skills'
    
    def __init__(self, readme_path: str):
        """Initialize the generator with path to README.md."""
        self.readme_path = Path(readme_path)
        self.skills: Dict[str, List[Dict]] = defaultdict(list)
        self.total_skills = 0
        self.created_dirs = 0
        self.created_files = 0
        self.errors = []
        
    def read_readme(self) -> str:
        """Read the README.md file."""
        try:
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"README.md not found at {self.readme_path}")
        except Exception as e:
            raise Exception(f"Error reading README.md: {e}")
    
    def parse_skills(self, content: str) -> None:
        """Parse all skill entries from README content."""
        lines = content.split('\n')
        
        for line in lines:
            match = re.match(self.SKILL_PATTERN, line)
            if match:
                skill_id, url, description = match.groups()
                
                # Parse provider and skill name
                parts = skill_id.split('/', 1)
                if len(parts) == 2:
                    provider, skill_name = parts
                    
                    skill = {
                        'id': skill_id,
                        'provider': provider,
                        'skill_name': skill_name,
                        'url': url.strip(),
                        'description': description.strip(),
                    }
                    
                    self.skills[provider].append(skill)
                    self.total_skills += 1
    
    def sanitize_path(self, name: str) -> str:
        """Sanitize a name to be filesystem-safe."""
        # Replace spaces and special chars with hyphens
        name = re.sub(r'[^\w\-]', '-', name)
        # Remove multiple consecutive hyphens
        name = re.sub(r'-+', '-', name)
        # Remove leading/trailing hyphens
        name = name.strip('-')
        return name.lower()
    
    def generate_skill_md(self, skill: Dict) -> str:
        """Generate the content of SKILL.md for a skill."""
        provider = skill['provider']
        skill_name = skill['skill_name']
        description = skill['description']
        url = skill['url']
        
        # Extract capability keywords from skill name and description
        keywords = self._extract_keywords(skill_name, description)
        
        # Infer when to use from description
        when_to_use = self._infer_when_to_use(description, skill_name)
        
        # Get related skills from same provider
        provider_skills = self.skills.get(provider, [])
        related = [s for s in provider_skills if s['skill_name'] != skill_name][:3]
        related_links = '\n'.join(
            [f"- [{s['skill_name'].replace('-', ' ').title()}](./{s['skill_name']}/SKILL.md)" 
             for s in related]
        ) if related else "- No related skills in this provider"
        
        # Build the SKILL.md content
        content = f"""# {provider.replace('-', ' ').title()} {skill_name.replace('-', ' ').title()}

## Overview

{description}

## When to Use

{when_to_use}

## Capability Keywords

- {chr(10).join(['- ' + kw for kw in keywords])}

## Description

This skill integrates {provider.replace('-', ' ')} capabilities for {skill_name.replace('-', ' ')} operations.

## Tool Requirements

- Authentication with {provider.replace('-', ' ')} (if required)
- API access and appropriate credentials
- Necessary dependencies installed

## Key Features

- {skill_name.replace('-', ' ').replace('_', ' ')}
- Integration with {provider.replace('-', ' ')} ecosystem
- Production-ready implementation

## Implementation Details

This skill provides structured access to {skill_name.replace('-', ' ')} functionality from the {provider.replace('-', ' ')} platform.

## Related Skills

{related_links}

## References

- **Official Documentation**: [{url}]({url})
- **Provider**: {provider.replace('-', ' ').title()}
- **Skill ID**: `{skill['id']}`

## Last Updated

{datetime.now().strftime('%Y-%m-%d')}
"""
        return content
    
    def _extract_keywords(self, skill_name: str, description: str) -> List[str]:
        """Extract capability keywords from skill name and description."""
        keywords = []
        
        # Add skill name parts as keywords
        name_parts = skill_name.split('-')
        keywords.extend([part for part in name_parts if len(part) > 2])
        
        # Extract important words from description
        words = re.findall(r'\b[A-Z][a-z]+\b', description)
        keywords.extend(words[:5])
        
        # Extract technical terms
        tech_terms = re.findall(r'\b(?:API|SDK|CLI|SQL|REST|JSON|XML|HTTP|HTTPS)\b', description, re.IGNORECASE)
        keywords.extend(tech_terms)
        
        # Remove duplicates and limit
        keywords = list(dict.fromkeys(keywords))[:8]
        
        return keywords if keywords else ['skill', skill_name.replace('-', ' ')]
    
    def _infer_when_to_use(self, description: str, skill_name: str) -> str:
        """Infer when to use the skill from its description."""
        if 'migrate' in description.lower() or 'migration' in description.lower():
            return f"Use this skill when you need to migrate or upgrade {skill_name.replace('-', ' ')} implementations."
        elif 'generate' in description.lower():
            return f"Use this skill to automatically generate {skill_name.replace('-', ' ')} code and configurations."
        elif 'test' in description.lower():
            return f"Use this skill to create and manage {skill_name.replace('-', ' ')} testing frameworks and suites."
        elif 'best practice' in description.lower() or 'guideline' in description.lower():
            return f"Use this skill for guidance on implementing {skill_name.replace('-', ' ')} best practices and standards."
        elif 'integrate' in description.lower() or 'integration' in description.lower():
            return f"Use this skill to integrate {skill_name.replace('-', ' ')} into your application or workflow."
        elif 'optimize' in description.lower():
            return f"Use this skill to optimize and improve {skill_name.replace('-', ' ')} performance and efficiency."
        else:
            return f"Use this skill when working with {skill_name.replace('-', ' ')} to enhance your development workflow."
    
    def create_directory_structure(self) -> None:
        """Create all directory structures and SKILL.md files."""
        base_path = Path(self.BASE_OUTPUT_DIR)
        
        try:
            # Create base directory
            base_path.mkdir(parents=True, exist_ok=True)
            self.created_dirs += 1
        except Exception as e:
            self.errors.append(f"Failed to create base directory: {e}")
            return
        
        # Create directory for each skill
        for provider, provider_skills in sorted(self.skills.items()):
            provider_dir = base_path / self.sanitize_path(provider)
            
            try:
                provider_dir.mkdir(parents=True, exist_ok=True)
                self.created_dirs += 1
            except Exception as e:
                self.errors.append(f"Failed to create provider dir {provider}: {e}")
                continue
            
            # Create skill-specific directories and files
            for skill in provider_skills:
                skill_dir = provider_dir / self.sanitize_path(skill['skill_name'])
                
                try:
                    skill_dir.mkdir(parents=True, exist_ok=True)
                    self.created_dirs += 1
                    
                    # Generate and write SKILL.md
                    skill_md_content = self.generate_skill_md(skill)
                    skill_file = skill_dir / 'SKILL.md'
                    
                    with open(skill_file, 'w', encoding='utf-8') as f:
                        f.write(skill_md_content)
                    
                    self.created_files += 1
                    
                except Exception as e:
                    self.errors.append(
                        f"Failed to create skill {skill['id']}: {e}"
                    )
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of all created skills."""
        report = []
        report.append("\n" + "=" * 80)
        report.append("AGENT SKILLS GENERATION REPORT")
        report.append("=" * 80 + "\n")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Statistics
        report.append("STATISTICS:")
        report.append("-" * 80)
        report.append(f"Total Skills Parsed:      {self.total_skills:,}")
        report.append(f"Total Providers:          {len(self.skills)}")
        report.append(f"Directories Created:      {self.created_dirs:,}")
        report.append(f"SKILL.md Files Generated: {self.created_files:,}\n")
        
        # Skills by provider
        report.append("SKILLS BY PROVIDER:")
        report.append("-" * 80)
        
        for provider in sorted(self.skills.keys()):
            count = len(self.skills[provider])
            report.append(f"  {provider:.<40} {count:>6} skills")
        
        report.append("")
        
        # Error handling
        if self.errors:
            report.append("WARNINGS AND ERRORS:")
            report.append("-" * 80)
            report.append(f"Total errors encountered: {len(self.errors)}\n")
            for i, error in enumerate(self.errors[:20], 1):  # Show first 20 errors
                report.append(f"  {i}. {error}")
            if len(self.errors) > 20:
                report.append(f"\n  ... and {len(self.errors) - 20} more errors")
            report.append("")
        
        # Completion message
        report.append("OUTPUT LOCATION:")
        report.append("-" * 80)
        report.append(f"Base directory: {Path(self.BASE_OUTPUT_DIR).absolute()}\n")
        
        report.append("STATUS: ✓ GENERATION COMPLETE")
        report.append("=" * 80 + "\n")
        
        return "\n".join(report)
    
    def generate_detailed_inventory(self, output_file: str = 'skills_inventory.txt') -> None:
        """Generate a detailed inventory of all skills."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("COMPREHENSIVE AGENT SKILLS INVENTORY\n")
                f.write("=" * 100 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Skills: {self.total_skills:,}\n")
                f.write(f"Total Providers: {len(self.skills)}\n")
                f.write("=" * 100 + "\n\n")
                
                for provider in sorted(self.skills.keys()):
                    f.write(f"\n{'─' * 100}\n")
                    f.write(f"PROVIDER: {provider.upper()}\n")
                    f.write(f"Count: {len(self.skills[provider])} skills\n")
                    f.write(f"{'─' * 100}\n\n")
                    
                    for skill in sorted(self.skills[provider], key=lambda x: x['skill_name']):
                        f.write(f"  📦 {skill['skill_name']}\n")
                        f.write(f"     ID: {skill['id']}\n")
                        f.write(f"     Desc: {skill['description'][:80]}...\n" 
                                if len(skill['description']) > 80 
                                else f"     Desc: {skill['description']}\n")
                        f.write(f"     URL: {skill['url']}\n")
                        f.write(f"     Dir: .github/skills/{self.sanitize_path(provider)}/{self.sanitize_path(skill['skill_name'])}/\n\n")
            
            print(f"✓ Detailed inventory written to: {output_file}")
        except Exception as e:
            self.errors.append(f"Failed to write inventory file: {e}")
    
    def run(self) -> bool:
        """Run the complete generation process."""
        print("🚀 Starting Agent Skills Generation...\n")
        
        try:
            # Read README
            print("📖 Reading README.md...")
            content = self.read_readme()
            print(f"✓ README.md loaded ({len(content)} chars)\n")
            
            # Parse skills
            print("🔍 Parsing skill entries...")
            self.parse_skills(content)
            print(f"✓ Found {self.total_skills:,} skills from {len(self.skills)} providers\n")
            
            # Create directories and files
            print("📁 Creating directory structure and generating SKILL.md files...")
            self.create_directory_structure()
            print(f"✓ Created {self.created_dirs:,} directories\n")
            print(f"✓ Generated {self.created_files:,} SKILL.md files\n")
            
            # Generate reports
            print("📊 Generating reports...")
            report = self.generate_summary_report()
            print(report)
            
            # Generate inventory
            self.generate_detailed_inventory()
            
            return len(self.errors) == 0
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate agent skills directory structure from README.md'
    )
    parser.add_argument(
        'readme',
        nargs='?',
        default='README.md',
        help='Path to README.md file (default: README.md)'
    )
    parser.add_argument(
        '--output-dir',
        default='.github/skills',
        help='Base output directory (default: .github/skills)'
    )
    parser.add_argument(
        '--inventory',
        default='skills_inventory.txt',
        help='Output file for detailed inventory (default: skills_inventory.txt)'
    )
    
    args = parser.parse_args()
    
    # Update base output directory if specified
    if args.output_dir != '.github/skills':
        SkillsGenerator.BASE_OUTPUT_DIR = args.output_dir
    
    # Run generator
    generator = SkillsGenerator(args.readme)
    success = generator.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
