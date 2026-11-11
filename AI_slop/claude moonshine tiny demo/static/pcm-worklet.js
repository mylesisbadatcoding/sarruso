// Captures mono Float32 PCM from the mic and posts ~100 ms chunks to the main thread.
class PcmCapture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buf = new Float32Array(1600);
    this.pos = 0;
  }
  process(inputs) {
    const input = inputs[0] && inputs[0][0];
    if (!input) return true;
    for (let i = 0; i < input.length; i++) {
      this.buf[this.pos++] = input[i];
      if (this.pos === this.buf.length) {
        const out = this.buf.slice(0);
        this.port.postMessage(out.buffer, [out.buffer]);
        this.pos = 0;
      }
    }
    return true;
  }
}
registerProcessor("pcm-capture", PcmCapture);
