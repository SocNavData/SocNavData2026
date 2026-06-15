# Survey selection process

This document describes how the survey selects video indices and their descriptions.

## Inputs

- app/static/videos/complete_indexed_videos: MP4 files named with zero-padded 9-digit IDs (1..MAX_VIDEOS).
- app/static/fixed_descriptions.json: Mapping of video_id -> description text.
- app/static/all_contexts.txt: Pool of possible description texts used to build the fixed mapping offline.
- app/static/tasks.py: Control question positions and fallback descriptions.
- app/static/surveycode.py: Runtime selection logic for each new session.

## Video index selection (per new session)

1. Create an indices list of length MAX_ANSWERS (currently 26).
2. Exclude the fixed control video IDs listed in tasks.FIXED_TASKS.
3. Randomly sample without replacement from the remaining IDs (1..MAX_VIDEOS minus fixed IDs).
4. Fill the indices list in order with the sampled IDs.
5. Apply fixed control positions and IDs using tasks.fix_fixed_tasks.

## Description selection

1. Load app/static/fixed_descriptions.json (via PyScript fetch or local file fallback).
2. For each index, look up the description by video_id.
3. Apply fixed control descriptions using the JSON mapping, falling back to the hardcoded defaults in tasks.FIXED_TASKS if the JSON entry is missing.
4. Choose a control_index from the non-fixed IDs and insert it at the beginning and end. The control description is also pulled from the JSON mapping, with a default fallback text.

## Notes

- The survey does not generate descriptions at runtime. The fixed_descriptions.json file is treated as the source of truth for descriptions.
- If fixed_descriptions.json is missing or has gaps, missing entries will be empty and fixed control entries will fall back to their default text.
- The random sampling is per session; the mapping makes the description text stable for any given video ID.

## Regenerating the description pool (offline)

- scripts/generate_tasks.py generates a full list of template descriptions in scripts/all_contexts.txt.
- app/static/all_contexts.txt is the pool used to build fixed_descriptions.json.
- The category-weighted sampling logic (including down-weighting lab and fire) is defined in app/static/tasks.py (see get_tasks_and_probabilities and generate_descriptions). The fixed mapping should follow the same weighting if you regenerate it.