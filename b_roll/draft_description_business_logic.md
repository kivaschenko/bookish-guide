the b-roll functionality is still present in the StoryForge codebase! Let me give you a detailed breakdown:
🎯 Current B-roll Options in exponential_video.py:

1. Vector-based B-roll Selection:
Location: src/b_roll_finder.py → prepare_brolls_vector() function
Functionality: Uses sentence transformers for semantic matching
Output: Generates broll_timing.json with synchronized B-rolls
Features:
Automatic B-roll extension in TTS mode to eliminate gaps
Vector-based selection using embeddings
Compatible with both Heygen and TTS audio modes

2. Metadata Extraction:
Location: src/meta_extractor.py
Functionality: Extracts metadata from B-roll videos using OpenAI Vision API
Output: Creates .txt files with video descriptions

3. B-roll Testing:
Location: src/b_roll_finder.py → test_broll_selection() function
Functionality: Tests B-roll selection for the first rush only

4. B-roll Cleanup:
Location: exponential_video.py → clean_broll_selections() function
Functionality: Cleans broll_selections.json by removing missing B-rolls
📁 Key Files for B-roll Module:
Core Files:
src/b_roll_finder.py - Main B-roll selection logic
src/vector_matcher.py - Vector-based matching
src/meta_extractor.py - Metadata extraction
Configuration:
config.yml - Contains B-roll settings (paths, durations, etc.)

🔧 To Create a Standalone B-roll Module:
You would need to extract and modularize:
src/b_roll_finder.py - Core B-roll selection logic
src/vector_matcher.py - Vector matching functionality
src/meta_extractor.py - Metadata extraction
Configuration handling - B-roll paths and settings
CLI interface - Similar to script_and_voice/module_script_and_voice.py

💡 Current Workflow:
--meta → Extract B-roll metadata
--vectorbroll → Select and time B-rolls
--testbrollchoice → Test selection (optional)