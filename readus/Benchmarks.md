# Benchmarks
There are a number of benchmarcks made for assessing text to speach models
Resouce: https://voiceping.net/en/blog/research-offline-speech-transcription-benchmark/
### Main benchmarks are:
- Inference: Wall-clock time from the recognition call to its result. Model download and initial loading are excluded in the Android source; this is not the time from installing the app to receiving a transcript.
- tok/s: The source apps use this label for an output-words-per-second estimate, not a count from a shared tokenizer. A partial or incorrect transcript can change the numerator, so this value must be read with completion status.
- RTF: Real-Time Factor—the processing time divided by audio duration. For example, 12 seconds to process 30 seconds of audio gives RTF 0.4. This does not measure the delay before a live caption first appears.
- Size: Approximate model-package download size. It is not peak process memory, and different exports of the same model can have different sizes.
- (WER/CER): Transcription accuracy.
