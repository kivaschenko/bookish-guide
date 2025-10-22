
# Manual Test Instructions

To verify the fix works with real audio generation:

1. Run the voice-only command:
   ```bash
   cd /home/kostiantyn/projects/storyforge
   venv/bin/python script_and_voice/module_script_and_voice.py \
     --project my-project-03 \
     --language french \
     --input-file ../projects/my-project-03/ori_vid.txt \
     --voice-only
   ```

2. Check that the command completes successfully (exit code 0)

3. Verify audio files are copied:
   ```bash
   ls -la projects/my-project-03/french/audio/
   ```
   Should contain: bullet_*.mp3, bullet_*.wav, audio_bullet_metadata.json

4. Run the full pipeline:
   ```bash
   venv/bin/python exponential_video.py -s my-project-04
   ```

Expected behavior:
- ✅ Script generation completes
- ✅ Voice generation completes 
- ✅ Audio files are copied to projects/my-project-04/french/audio/
- ✅ No "Voice generation failed" error
- ✅ Process completes successfully

## What the fix does:

The original issue was that `gemini_tts.generate_all_audio()` returned metadata directly:
```python
return metadata  # Just the metadata dict
```

But `module_script_and_voice.py` expected a result with success flag:
```python
if not voice_result.get("success"):  # This was always True (failure)
```

The fix makes `generate_all_audio()` return:
```python
return {
    "success": True,
    "total_duration": cumulative_time,
    "total_bullets": len(bullets),
    "audio_files": [b["audio_file"] for b in metadata["bullets"]],
    "metadata_file": str(metadata_path),
    "metadata": metadata
}
```

This allows the success check to pass and file copying to proceed.
