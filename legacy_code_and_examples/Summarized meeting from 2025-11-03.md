Summarized meeting from 2025-11-03
K dev Impromptu Google Meet Meeting - November 03
VIEW RECORDING: 
Meeting Purpose

Align on the video creation project's architecture and next steps.

Key Takeaways

  - Goal: Create 40 videos to reach YouTube's 1k subscriber monetization threshold.
  - Core Logic: The system automates B-roll selection. For each sentence, a vector DB finds 10 candidates, an LLM picks the top 3, and a human editor makes the final choice.
  - Architecture: Kostiantyn will audit Erwin's two existing servers (Editing & Dashboard) to decide whether to fix the old code or integrate the editing logic into Kostiantyn's cleaner, multi-user prototype.
  - Deliverable: The project's sole output is a b-roll_timing.json timeline file, which a separate, functional MoviePy script then uses to compile the final video.

Topics

Current State & Prototype

  - Kostiantyn demoed a multi-user MVP prototype (multi-user-MVP branch) with a Vue.js frontend and Python backend.
  - Functionality: User auth, project creation, and B-roll upload with AI metadata generation.
  - Technical Issue: A Bycrypt package version conflict is preventing user login.

Business Logic & Workflow

  - Erwin outlined the core workflow, which automates B-roll selection to accelerate video production.
  - Workflow:
    1.  Script Processing: A script is split into sentences.
    2.  B-roll Retrieval: A vector DB finds 10 B-roll candidates per sentence.
    3.  LLM Selection: An LLM (e.g., ChatGPT) ranks the 10 candidates, selecting the top 3 based on their AI descriptions.
    4.  Human Editing: An assistant uses a UI to choose the best B-roll from the top 3.
          - Rationale: Human oversight is critical to prevent nonsensical AI choices (e.g., a tombstone for a 100-year-old person).
          - Alternatives: The assistant can also upload a static image (e.g., a photo of Warren Buffett) instead of using B-roll.
    5.  Timeline Generation: The UI auto-saves all choices to the b-roll_timing.json file.

Architecture Decision: Prototype vs. New Build

  - The team must decide whether to fix Erwin's existing code or integrate the editing logic into Kostiantyn's cleaner prototype.
  - Erwin's Existing System:
      - Two separate servers: an Editing server and a Dashboard server.
      - Code is functional but "dirty," having been built with heavy LLM assistance.
      - The Dashboard server includes an admin panel for managing project steps and tasks.
  - Kostiantyn's Prototype:
      - Cleaner, modular code with a modern tech stack (Vue.js, Python).
      - Includes multi-user authentication, which could be useful for managing multiple channels.
  - Decision Criteria:
      - Prototype Focus: The immediate goal is a cheap, fast prototype to produce 40 videos, not a professional product.
      - Kostiantyn's Role: Kostiantyn will audit Erwin's codebase to determine the most efficient path forward.

Timeline File (b-roll_timing.json)

  - This JSON file is the project's central output and the input for the final video compilation.
  - Structure:
      - rush (paragraph) → phrase (sentence) → audio (MP3 file)
      - selected_b_roll: The human-chosen B-roll clip.
      - b_roll_2, b_roll_3: The LLM's second and third choices.
      - image: An optional field for a static image.
  - Current Limitation: The system uses one MP3 per paragraph, which limits precise timing. A future improvement could be one MP3 per sentence.

Next Steps

  - Erwin:
      - Share the Dashboard server codebase via Google Drive.
      - Provide ~200 B-roll videos and a sample b-roll_timing.json file for end-to-end testing.
      - Share the meeting transcript and recording.
  - Kostiantyn:
      - Audit Erwin's codebase to assess the effort required to fix it vs. building new.
      - Propose a path forward via Signal tomorrow.
