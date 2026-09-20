import math
import struct
import wave

def generate_lofi_track(filename="lofi_music.wav", duration_sec=30, sample_rate=44100):
    num_samples = int(duration_sec * sample_rate)
    
    # Lo-fi Chord Progression: Cmaj7, Am7, Dm7, G7 (repeating every 4 seconds)
    # Frequencies for notes
    C3, E3, G3, B3 = 130.81, 164.81, 196.00, 246.94
    A2, C3_a, E3_a, G3_a = 110.00, 130.81, 164.81, 196.00
    D3, F3, A3, C4 = 146.83, 174.61, 220.00, 261.63
    G2, B2, D3_g, F3_g = 98.00, 123.47, 146.83, 174.61
    
    chords = [
        [C3, E3, G3, B3],
        [A2, C3_a, E3_a, G3_a],
        [D3, F3, A3, C4],
        [G2, B2, D3_g, F3_g]
    ]

    wav_file = wave.open(filename, "w")
    wav_file.setnchannels(2)  # Stereo
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)

    frames = bytearray()

    bpm = 85
    beat_duration = 60.0 / bpm  # ~0.705s per beat
    bar_duration = beat_duration * 4  # ~2.82s per bar

    for i in range(num_samples):
        t = i / sample_rate

        # Chord selection
        bar_idx = int(t / bar_duration) % 4
        current_chord = chords[bar_idx]
        
        # Soft chord synth with gentle envelope
        chord_val = 0.0
        for freq in current_chord:
            # Low-pass effect using fundamental + soft 2nd harmonic
            tone = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)
            chord_val += tone
        chord_val *= 0.15

        # Lo-fi Drums: Kick, Snare, Hi-hat
        beat_t = t % beat_duration
        sub_beat = (t % (beat_duration / 2))

        # Kick on beat 1 and beat 3 (decaying low sine)
        kick_val = 0.0
        beat_num = int(t / beat_duration) % 4
        if beat_num in (0, 2) and beat_t < 0.15:
            kick_freq = 60 * (1 - beat_t / 0.15) + 30
            kick_val = math.sin(2 * math.pi * kick_freq * beat_t) * (1 - beat_t / 0.15) * 0.5

        # Snare on beat 2 and beat 4 (noise-like snap)
        snare_val = 0.0
        if beat_num in (1, 3) and beat_t < 0.12:
            import random
            noise = (random.random() - 0.5) * 2
            snare_val = noise * (1 - beat_t / 0.12) * 0.25

        # Hi-hat on every 8th note
        hihat_val = 0.0
        if sub_beat < 0.04:
            import random
            hihat_val = (random.random() - 0.5) * (1 - sub_beat / 0.04) * 0.08

        # Vinyl crackle simulation
        import random
        crackle = (random.random() - 0.5) * 0.015 if random.random() < 0.05 else 0

        # Combine all parts
        sample_val = chord_val + kick_val + snare_val + hihat_val + crackle
        
        # Master volume & clipping protection
        sample_val = max(-0.95, min(0.95, sample_val))

        # Convert to 16-bit PCM integer
        int_sample = int(sample_val * 32767)
        packed_sample = struct.pack("<h", int_sample)
        
        # Write left and right channels
        frames.extend(packed_sample)
        frames.extend(packed_sample)

    wav_file.writeframes(frames)
    wav_file.close()
    print(f"Generated {filename} successfully ({duration_sec}s).")

if __name__ == "__main__":
    generate_lofi_track()
