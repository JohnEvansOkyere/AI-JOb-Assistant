# Bias & Fairness Guidelines

## Core Principles

The AI interviewer must **never** ask about or consider:

- Age
- Gender
- Religion
- Ethnicity
- Marital status
- Health/disabilities
- Political affiliation
- Sexual orientation
- Family status (children, etc.)

## Allowed Focus Areas

The interview should focus exclusively on:

1. **Technical Skills**
   - Programming languages
   - Tools and frameworks
   - Certifications
   - Technical knowledge

2. **Experience**
   - Years of experience (in role/field)
   - Previous projects
   - Responsibilities
   - Achievements

3. **Soft Skills**
   - Communication
   - Problem-solving
   - Collaboration
   - Leadership
   - Time management

4. **Role Relevance**
   - Match to job requirements
   - Domain knowledge
   - Industry experience

## Implementation

### Prompt Engineering

All AI prompts must include explicit instructions to:
- Avoid protected characteristics
- Focus on job-relevant criteria
- Ask clarifying questions if information is missing
- Never make assumptions about candidate background

### Response Filtering

- Filter out any questions that reference protected characteristics
- Monitor AI responses for bias indicators
- Log and flag potential bias issues

### Scoring

- Scoring algorithms must exclude any demographic data
- Reports must not contain demographic inferences
- Focus on skill match and role fit only

## Monitoring

- Regular audits of generated questions
- Review of interview reports for bias
- Candidate feedback collection
- Continuous improvement of prompts

