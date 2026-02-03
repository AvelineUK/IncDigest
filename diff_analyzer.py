"""
Diff Analysis Module
Compares two versions of a 10-K section and identifies meaningful changes
"""

import difflib
from typing import Dict, List, Tuple
import re


class DiffAnalyzer:
    """Analyzes differences between two versions of text"""
    
    def __init__(self):
        self.min_change_length = 50  # Ignore changes shorter than this (minor wording)
    
    def clean_text(self, text: str) -> str:
        """
        Clean text for comparison
        - Normalize whitespace
        - Remove excessive newlines
        - Preserve paragraph structure
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def get_text_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks for comparison
        Uses sentences when possible to avoid breaking mid-sentence
        """
        # Split into sentences (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def compute_diff(self, old_text: str, new_text: str) -> Dict:
        """
        Compute differences between old and new text
        Returns structured diff with additions, deletions, and unchanged portions
        """
        old_clean = self.clean_text(old_text)
        new_clean = self.clean_text(new_text)
        
        # Use difflib to get differences at line level
        old_lines = old_clean.split('\n')
        new_lines = new_clean.split('\n')
        
        differ = difflib.Differ()
        diff = list(differ.compare(old_lines, new_lines))
        
        additions = []
        deletions = []
        unchanged = []
        
        for line in diff:
            if line.startswith('+ '):
                additions.append(line[2:])
            elif line.startswith('- '):
                deletions.append(line[2:])
            elif line.startswith('  '):
                unchanged.append(line[2:])
        
        return {
            'additions': '\n'.join(additions),
            'deletions': '\n'.join(deletions),
            'unchanged': '\n'.join(unchanged),
            'has_changes': bool(additions or deletions)
        }
    
    def get_unified_diff(self, old_text: str, new_text: str, context_lines: int = 3) -> str:
        """
        Generate unified diff format (like git diff)
        Shows changes with surrounding context
        """
        old_clean = self.clean_text(old_text)
        new_clean = self.clean_text(new_text)
        
        old_lines = old_clean.split('\n')
        new_lines = new_clean.split('\n')
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=context_lines
        )
        
        return '\n'.join(diff)
    
    def extract_meaningful_changes(self, old_text: str, new_text: str) -> Dict:
        """
        Extract only meaningful changes, filtering out minor wording changes
        Optimized for large sections (like Item 8 Financial Statements)
        
        Returns:
        - added_content: Text that was added
        - removed_content: Text that was removed
        - modified_sections: Sections that were substantially modified
        """
        # For very large sections (>100K chars), use simpler comparison
        if len(old_text) > 100000 or len(new_text) > 100000:
            print(f"    Large section detected ({len(old_text):,} / {len(new_text):,} chars), using fast comparison...")
            
            # Simple approach: just note that it changed
            # For financial statements, detailed diff isn't as useful anyway
            return {
                'added_content': new_text[:5000],  # First 5K chars as sample
                'removed_content': old_text[:5000],
                'has_meaningful_changes': True,
                'summary': f'Large section: ~{len(new_text):,} chars in new version vs ~{len(old_text):,} chars in old version'
            }
        
        diff = self.compute_diff(old_text, new_text)
        
        if not diff['has_changes']:
            return {
                'added_content': '',
                'removed_content': '',
                'has_meaningful_changes': False,
                'summary': 'No material changes detected'
            }
        
        added = diff['additions']
        removed = diff['deletions']
        
        # Filter out very short changes (likely just minor wording)
        if len(added) < self.min_change_length and len(removed) < self.min_change_length:
            return {
                'added_content': '',
                'removed_content': '',
                'has_meaningful_changes': False,
                'summary': 'Only minor wording changes detected'
            }
        
        return {
            'added_content': added,
            'removed_content': removed,
            'has_meaningful_changes': True,
            'summary': f'Changes detected: ~{len(added)} chars added, ~{len(removed)} chars removed'
        }
    
    def compare_sections(self, old_sections: Dict[str, str], 
                        new_sections: Dict[str, str]) -> Dict[str, Dict]:
        """
        Compare all sections between two filings
        
        Args:
            old_sections: Dict mapping section names to content (older filing)
            new_sections: Dict mapping section names to content (newer filing)
        
        Returns:
            Dict mapping section names to their diff analysis
        """
        results = {}
        
        # Get all section names
        all_sections = set(old_sections.keys()) | set(new_sections.keys())
        
        for section_name in all_sections:
            old_content = old_sections.get(section_name, '')
            new_content = new_sections.get(section_name, '')
            
            if not old_content and not new_content:
                continue
            elif not old_content:
                # Section was added
                results[section_name] = {
                    'status': 'added',
                    'added_content': new_content,
                    'removed_content': '',
                    'has_meaningful_changes': True,
                    'summary': 'Entire section is new'
                }
            elif not new_content:
                # Section was removed
                results[section_name] = {
                    'status': 'removed',
                    'added_content': '',
                    'removed_content': old_content,
                    'has_meaningful_changes': True,
                    'summary': 'Entire section was removed'
                }
            else:
                # Section exists in both, compare
                changes = self.extract_meaningful_changes(old_content, new_content)
                changes['status'] = 'modified' if changes['has_meaningful_changes'] else 'unchanged'
                results[section_name] = changes
        
        return results
    
    def generate_diff_report(self, section_name: str, diff_result: Dict) -> str:
        """
        Generate a human-readable diff report for a section
        """
        status = diff_result['status']
        
        if status == 'unchanged':
            return f"{section_name}: No material changes"
        
        report = f"\n{'='*60}\n"
        report += f"{section_name}\n"
        report += f"{'='*60}\n\n"
        report += f"Status: {status.upper()}\n"
        report += f"Summary: {diff_result['summary']}\n\n"
        
        if diff_result.get('removed_content'):
            report += "--- REMOVED CONTENT ---\n"
            report += diff_result['removed_content'][:500]  # Truncate for display
            if len(diff_result['removed_content']) > 500:
                report += "\n... (truncated)"
            report += "\n\n"
        
        if diff_result.get('added_content'):
            report += "+++ ADDED CONTENT +++\n"
            report += diff_result['added_content'][:500]  # Truncate for display
            if len(diff_result['added_content']) > 500:
                report += "\n... (truncated)"
            report += "\n\n"
        
        return report


if __name__ == "__main__":
    # Test with sample text
    old_text = """
    Risk Factor 1: Market Competition
    We face intense competition in our industry. Our competitors include large technology companies
    with significant resources. If we fail to compete effectively, our business may suffer.
    
    Risk Factor 2: Regulatory Changes
    We are subject to various regulations. Changes in regulations could impact our operations.
    """
    
    new_text = """
    Risk Factor 1: Market Competition and AI Disruption
    We face intense competition in our industry, particularly from emerging AI-powered competitors.
    Our competitors include large technology companies with significant resources and new startups
    with innovative AI capabilities. If we fail to compete effectively or adapt to AI disruption,
    our business may suffer materially.
    
    Risk Factor 2: Regulatory Changes
    We are subject to various regulations including new AI safety requirements. Changes in 
    regulations could significantly impact our operations and require substantial compliance costs.
    
    Risk Factor 3: Cybersecurity Threats
    We face increasing cybersecurity threats from sophisticated actors. A breach could result
    in significant financial and reputational damage.
    """
    
    analyzer = DiffAnalyzer()
    
    print("Testing diff analysis...")
    changes = analyzer.extract_meaningful_changes(old_text, new_text)
    
    print(f"\nHas meaningful changes: {changes['has_meaningful_changes']}")
    print(f"Summary: {changes['summary']}")
    print("\nAdded content (truncated):")
    print(changes['added_content'][:300])
