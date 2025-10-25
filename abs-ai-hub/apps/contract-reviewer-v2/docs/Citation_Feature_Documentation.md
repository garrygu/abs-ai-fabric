# Citation Feature Documentation

## Overview
The Contract Reviewer v2 now includes comprehensive citation functionality that provides detailed references for every analysis finding. This ensures legal professionals can verify AI analysis against actual document content and maintain professional standards.

## Citation Structure

### Key Points with Citations
Each key point includes:
- **Point**: Description of the key finding
- **Citation**: Specific section/clause reference
- **Importance**: Priority level (high/medium/low)
- **Text Excerpt**: Exact text from the document

```json
{
    "point": "Unlimited liability exposure for ABC Corp",
    "citation": "Section 4.2, Page 3",
    "importance": "high",
    "text_excerpt": "ABC Corp shall be liable for all damages arising from breach of confidentiality obligations without limitation."
}
```

### Risk Analysis with Citations
Each risk includes:
- **Level**: Risk severity (high/medium/low)
- **Description**: Risk description
- **Section**: Relevant section or clause
- **Citation**: Specific text excerpt or reference
- **Impact**: Potential impact description
- **Text Excerpt**: Exact text from document

```json
{
    "level": "high",
    "description": "Unlimited liability exposure for ABC Corp",
    "section": "Section 4.2",
    "citation": "Section 4.2, Page 3",
    "impact": "Potential unlimited financial exposure",
    "text_excerpt": "ABC Corp shall be liable for all damages arising from breach of confidentiality obligations without limitation."
}
```

### Recommendations with Citations
Each recommendation includes:
- **Recommendation**: Specific recommendation
- **Rationale**: Why this recommendation is important
- **Citation**: Relevant section that supports this recommendation
- **Priority**: Priority level (high/medium/low)
- **Text Excerpt**: Supporting text from document

```json
{
    "recommendation": "Add liability cap of $100,000",
    "rationale": "Protects against unlimited financial exposure",
    "citation": "Section 4.2",
    "priority": "high",
    "text_excerpt": "Neither party's liability shall exceed $100,000 for any breach of confidentiality obligations."
}
```

### Key Clauses Analysis
Each clause includes:
- **Clause**: Clause description
- **Type**: Type of clause (liability/termination/payment/confidentiality/etc)
- **Citation**: Exact text or section reference
- **Significance**: Why this clause is important
- **Text Excerpt**: Full clause text

```json
{
    "clause": "Confidentiality Obligations",
    "type": "confidentiality",
    "citation": "Section 2.1, Page 2",
    "significance": "Core purpose of the agreement",
    "text_excerpt": "Each party agrees to maintain confidentiality of all proprietary information disclosed during the term of this agreement."
}
```

### Compliance Issues with Citations
Each compliance issue includes:
- **Issue**: Compliance issue description
- **Standard**: Which standard/regulation (GDPR/CCPA/SOX/etc)
- **Citation**: Specific section or clause
- **Severity**: Severity level (high/medium/low)
- **Text Excerpt**: Relevant text from document

```json
{
    "issue": "Missing data retention policy",
    "standard": "GDPR",
    "citation": "Article 5(1)(e) - data minimization principle",
    "severity": "medium",
    "text_excerpt": "Personal data shall be kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed."
}
```

## Citation Standards

### Section References
- **Format**: "Section 3.2", "Clause 5.1", "Page 3"
- **Hierarchy**: Section → Subsection → Clause → Paragraph
- **Examples**: 
  - "Section 4.2"
  - "Clause 5.1.3"
  - "Page 3, Paragraph 2"

### Text Excerpts
- **Exact Quotes**: Use exact text from the document
- **Context**: Include enough context to understand the meaning
- **Length**: Typically 1-3 sentences for clarity
- **Formatting**: Preserve original formatting and punctuation

### Location Data
- **Page Numbers**: When available
- **Line References**: For detailed analysis
- **Paragraph Numbers**: For structured documents
- **Section Identifiers**: For legal documents

## AI Prompt Enhancement

The AI analysis prompt now specifically requests:

1. **Detailed Citations**: For every finding, include specific section/clause references
2. **Text Excerpts**: Provide exact quotes from the document
3. **Location Data**: Include page numbers, paragraph references, and line numbers
4. **Context**: Explain why each finding is important
5. **Supporting Evidence**: Show how recommendations are supported by document content

## Database Storage

### PostgreSQL JSONB Structure
The `analysis_data` field in the `analysis_results` table stores the complete citation-enhanced analysis:

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_data JSONB NOT NULL,  -- Enhanced with citations
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    confidence_score FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'completed',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### JSONB Indexing
PostgreSQL's JSONB support allows for efficient querying of citation data:

```sql
-- Index for searching by citation content
CREATE INDEX idx_analysis_citations ON analysis_results USING GIN ((analysis_data->'risks'));

-- Index for searching by compliance issues
CREATE INDEX idx_analysis_compliance ON analysis_results USING GIN ((analysis_data->'compliance'->'compliance_issues'));
```

## Benefits

### Legal Professional Benefits
- **Verification**: Every finding can be verified against source document
- **Traceability**: Complete audit trail of analysis sources
- **Accuracy**: Reduces risk of misinterpretation
- **Professional Standards**: Meets legal analysis best practices

### System Benefits
- **Transparency**: Clear understanding of AI reasoning
- **Quality Control**: Easy to validate analysis accuracy
- **Compliance**: Supports regulatory and audit requirements
- **User Trust**: Builds confidence in AI analysis

### Operational Benefits
- **Efficiency**: Faster verification and review process
- **Consistency**: Standardized citation format across all analyses
- **Scalability**: Structured data supports automated processing
- **Integration**: Easy integration with legal workflow tools

## Implementation Notes

### Backward Compatibility
- Existing analyses without citations continue to work
- New analyses automatically include citations
- Fallback data structure includes basic citation information

### Performance Considerations
- JSONB storage is efficient for complex citation structures
- Indexing supports fast queries on citation content
- Caching reduces repeated citation processing

### Quality Assurance
- AI prompt specifically requests detailed citations
- Fallback mechanisms ensure citations are always provided
- Validation ensures citation format consistency

## Future Enhancements

### Planned Features
- **Citation Validation**: Verify citations against document content
- **Cross-Reference Analysis**: Link related citations across documents
- **Citation Templates**: Standardized citation formats for different document types
- **Citation Analytics**: Track citation patterns and accuracy

### Integration Opportunities
- **Legal Research Tools**: Integration with Westlaw, LexisNexis
- **Document Management**: Integration with legal document management systems
- **Compliance Monitoring**: Automated compliance checking based on citations
- **Risk Assessment**: Enhanced risk analysis using citation patterns

This citation feature significantly enhances the value and reliability of the Contract Reviewer v2 analysis, providing legal professionals with the detailed references they need to make informed decisions.

