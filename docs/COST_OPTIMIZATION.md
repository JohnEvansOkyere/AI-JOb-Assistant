# Cost Optimization Strategy

## Token Management

### Per-Interview Limits

- **Default**: 50,000 tokens per interview
- **Hard Cap**: 75,000 tokens (with warning)
- **Model Selection**: Use cost-optimized models (GPT-4o-mini, Gemini Flash)

### Token Tracking

- Track tokens used per interview
- Stop interview if limit exceeded
- Log token usage for analysis

## Interview Duration

- **Default**: 20 minutes
- **Maximum**: 30 minutes
- **Auto-end**: When time limit reached
- **Early completion**: Allow candidate to finish early

## Streaming

- Use streaming APIs for:
  - TTS (ElevenLabs streaming)
  - STT (real-time transcription)
  - AI responses (streaming completions)

## Caching

- Cache parsed CVs (avoid re-parsing)
- Cache job description embeddings
- Cache common question templates

## Audio Management

- **During Interview**: Store temporarily
- **After Processing**: 
  - Generate transcript
  - Archive audio (optional)
  - Delete after 30 days (configurable)

## Model Selection

### Cost Tiers

1. **Question Generation**: GPT-4o-mini / Gemini Flash
2. **Response Analysis**: GPT-4o-mini / Gemini Flash
3. **Report Generation**: GPT-4o-mini (sufficient for structured output)

### Fallback Strategy

- Primary: GPT-4o-mini
- Fallback 1: Groq (fast, cheap)
- Fallback 2: Gemini Flash

## Monitoring

- Track costs per interview
- Set monthly budget alerts
- Analyze token usage patterns
- Optimize prompts to reduce tokens

## Configuration

All cost-related settings in `.env`:

```env
MAX_TOKENS_PER_INTERVIEW=50000
MAX_INTERVIEW_DURATION_SECONDS=1800
DEFAULT_INTERVIEW_DURATION_SECONDS=1200
AUDIO_RETENTION_DAYS=30
```

