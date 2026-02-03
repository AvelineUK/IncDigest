"""
Quality Validator
Checks if extraction meets quality standards
Determines if user should get automatic refund
"""


class QualityValidator:
    """
    Validates extraction quality to determine if refund needed
    
    This is critical for the Beta launch strategy:
    - Auto-detect poor extractions
    - Issue refund automatically
    - Still provide the report
    - Log for debugging
    """
    
    def __init__(self):
        # Minimum word counts for each section
        # Based on testing, these are reasonable thresholds
        self.min_word_counts = {
            'Item 1': 1000,     # Business section
            'Item 1A': 3000,    # Risk Factors (usually longest)
            'Item 7': 3000,     # MD&A
            'Item 8': 2000      # Financial Statements (lowered - some are pointers)
        }
    
    def validate_extraction(self, filings, diff_results, ai_results):
        """
        Check if extraction meets quality standards
        
        Args:
            filings: List of filing dicts with sections
            diff_results: Results from diff analysis
            ai_results: Results from AI analysis
        
        Returns:
            {
                'is_valid': bool,  # True if passes all checks
                'issues': [list of issue descriptions]
            }
        """
        issues = []
        
        # ========================================
        # CHECK 1: All required sections present
        # ========================================
        required_sections = ['Item 1', 'Item 1A', 'Item 7', 'Item 8']
        
        for i, filing in enumerate(filings):
            filing_label = "newer" if i == 0 else "older"
            missing = [s for s in required_sections if s not in filing['sections']]
            
            if missing:
                issues.append(
                    f"{filing_label.capitalize()} filing: Missing sections {', '.join(missing)}"
                )
        
        # ========================================
        # CHECK 2: Minimum content length
        # ========================================
        # CRITICAL: We care most about the NEWER filing (index 0)
        # Only flag if newer filing has issues, or both have same issue
        for i, filing in enumerate(filings):
            filing_label = "newer" if i == 0 else "older"
            
            for section_name, content in filing['sections'].items():
                if section_name in self.min_word_counts:
                    word_count = len(content.split())
                    min_words = self.min_word_counts[section_name]
                    
                    if word_count < min_words:
                        # Only add issue if:
                        # 1. It's the newer filing (most important), OR
                        # 2. Both filings have the same section too short
                        if i == 0:  # Newer filing
                            issues.append(
                                f"{section_name} ({filing_label}): Only {word_count:,} words "
                                f"(expected {min_words:,}+) - CRITICAL: Newer filing extraction failed"
                            )
                        else:  # Older filing - check if newer also has issue
                            newer_content = filings[0]['sections'].get(section_name, '')
                            newer_word_count = len(newer_content.split())
                            if newer_word_count < min_words:
                                # Both filings have issue - this is a problem
                                issues.append(
                                    f"{section_name}: Both filings too short "
                                    f"(newer: {newer_word_count:,}, older: {word_count:,}, expected {min_words:,}+)"
                                )
                            # If only older filing short, don't flag - AI can still compare
        
        # ========================================
        # CHECK 3: Content quality (not all tables)
        # ========================================
        # If extraction got tables instead of text, it's mostly numbers
        # Again, prioritize newer filing issues
        for i, filing in enumerate(filings):
            filing_label = "newer" if i == 0 else "older"
            
            for section_name, content in filing['sections'].items():
                words = content.split()
                if len(words) > 100:  # Only check if we have enough words
                    # Count how many words contain digits
                    number_words = sum(1 for w in words if any(c.isdigit() for c in w))
                    number_ratio = number_words / len(words)
                    
                    if number_ratio > 0.8:
                        # Only flag if newer filing, or both have issue
                        if i == 0:  # Newer filing
                            issues.append(
                                f"{section_name} ({filing_label}): Appears to be mostly "
                                f"tables/numbers ({number_ratio:.0%} numeric content) - CRITICAL"
                            )
                        else:  # Older filing - check if newer also has issue
                            newer_content = filings[0]['sections'].get(section_name, '')
                            newer_words = newer_content.split()
                            if len(newer_words) > 100:
                                newer_number_words = sum(1 for w in newer_words if any(c.isdigit() for c in w))
                                newer_ratio = newer_number_words / len(newer_words)
                                if newer_ratio > 0.8:
                                    issues.append(
                                        f"{section_name}: Both filings appear to be mostly tables "
                                        f"({newer_ratio:.0%} / {number_ratio:.0%} numeric)"
                                    )
        
        # ========================================
        # CHECK 4: AI summaries generated
        # ========================================
        if not ai_results.get('summaries'):
            issues.append("No AI summaries generated")
        else:
            # Check each required section has a summary
            for section in required_sections:
                if section not in ai_results['summaries']:
                    issues.append(f"Missing AI summary for {section}")
                elif len(ai_results['summaries'][section]) < 50:
                    issues.append(f"{section}: AI summary too short")
                
                # Future enhancement: Could add universal hallucination detection here
                # For now, rely on extraction quality checks only
                # Product names vary by company and change over time
        
        # ========================================
        # CHECK 5: Diff analysis ran
        # ========================================
        if not diff_results:
            issues.append("Diff analysis did not run")
        
        # ========================================
        # RETURN RESULT
        # ========================================
        is_valid = len(issues) == 0
        
        return {
            'is_valid': is_valid,
            'issues': issues
        }
