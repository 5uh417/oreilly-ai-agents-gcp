# Self-Improving Image Generation with LoopAgent

**Source**: This code is adapted from the [ADK Samples Repository](https://github.com/google/adk-samples/tree/main/python/agents/image-scoring) for educational purposes.

**Attribution**: Original implementation by the Google ADK team. Replicated here for the O'Reilly AI Agents course lab exercise.

## Quick Start

1. Add your Google AI Studio API key to `.env`
2. Run `adk web` and select `solution` from the dropdown
3. Try prompts like: "Create a stunning mountain landscape for a mobile lockscreen"

## What This Demonstrates

This system shows how LoopAgent patterns enable iterative improvement:
- Generates images with Imagen 3.0
- Scores quality against multiple criteria (0-50 points)
- Automatically iterates until quality threshold (45+) is met or max attempts (3) reached
- Uses proper ADK escalation mechanisms for loop control

The code will continue to be maintained in the original ADK samples repository.