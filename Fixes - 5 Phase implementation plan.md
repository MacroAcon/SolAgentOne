Here is a 5-phase implementation plan designed to address the recommendations and bring your agentic content creation system up to date and into a stable, working state.

### **Phase 1: Critical Workflow and Logic Fixes**

**Objective:** Address the fatal logical errors in `orchestrator.py` to make the primary workflow executable from start to finish. This phase focuses on making the system run without crashing due to internal inconsistencies.

* **Tasks:**  
  1. **Integrate Synthesis Agent:** In `orchestrator.py`, call the `develop_narrative_theme` function from the `synthesis_agent` to generate the weekly `narrative_brief`.  
  2. **Correct Generator Calls:** Pass the generated `narrative_brief` as an argument to `generate_podcast_script` and `generate_newsletter_content` as required by their function definitions.  
  3. **Activate Audio Generation:** Integrate the `tts_agent` by calling `generate_audio_from_script` after the podcast script is successfully created.  
  4. **Fix Podcast Upload Logic:** Modify the `upload_to_spotify` call to pass the file path of the newly generated `.mp3` audio file, not the `.txt` script file.  
  5. **Correct Function Calls:**  
     * Fix the image generator call to use the correct function name: `create_newsletter_image`.  
     * Adjust the arguments passed to `update_publication_log` to match the function's definition (`campaign_id`, `episode_id`, etc.).  
  6. **Route Community Data Correctly:** Ensure the `featured_posts` list returned by the `researcher_agent` is passed to the `post_engagement_comments` function, not the social publisher.

### **Phase 2: Code Standardization and Refactoring**

**Objective:** Improve code quality, consistency, and long-term maintainability by standardizing API usage and removing duplicated code.

* **Tasks:**  
  1. **Standardize OpenAI API Usage:** Update `newsletter_generator.py`, `researcher.py`, and `script_generator.py` to use the modern client-based syntax for the OpenAI API (`client = OpenAI(...)`, `client.chat.completions.create()`). This will make them consistent with `analytics_agent.py` and `quality_agent.py`.  
  2. **Create a Utility Module:** Create a new file named `utils.py`.  
  3. **Refactor `read_content_files`:** Move the duplicated `read_content_files` function into the new `utils.py` module.  
  4. **Update Imports:** Change `script_generator.py` and `newsletter_generator.py` to import the `read_content_files` function from `utils.py`.  
  5. **Code Cleanup:** Perform a pass on all `.py` files to remove unused import statements.

### **Phase 3: External API Migration (Spotify for Podcasters)**

**Objective:** Replace the legacy Anchor.fm API calls with the modern, officially supported Spotify for Podcasters API to ensure future stability and access to new features.

* **Tasks:**  
  1. **API Research:** Consult the official Spotify for Podcasters API documentation to identify the current endpoints, authentication methods, and data schemas for uploading audio and fetching episode statistics.  
  2. **Update Publisher Agent:** Rewrite the `upload_to_spotify` function in `publisher.py` to use the new API endpoints. This may require changes to function arguments and the handling of the API response.  
  3. **Update Analytics Agent:** Rewrite the `get_spotify_stats` function in `analytics_agent.py` to fetch data from the new analytics endpoints.  
  4. **Update Configuration:** Add any new API keys or credentials required by the new API to the `.env` file and update the code to load them.

### **Phase 4: Deprecated Library Replacement (LinkedIn)**

**Objective:** Address the fragile LinkedIn integration by replacing the unmaintained `linkedin-api` library with a more stable and reliable solution.

* **Tasks:**  
  1. **Research Alternatives:** Investigate robust alternatives for posting to LinkedIn, such as officially supported partner APIs (e.g., Unipile) or other third-party social media management services that provide stable client libraries.  
  2. **Select and Implement:** Choose a replacement based on reliability, cost, and features. Rewrite the `_publish_to_linkedin` function in `social_publisher.py` to integrate the new library or API service.  
  3. **Update Dependencies:** Remove `linkedin-api` from `requirements.txt` and add the new dependency if applicable.

### **Phase 5: Final Review, End-to-End Testing, and Documentation**

**Objective:** Ensure all changes are integrated correctly, the system is fully functional, and the documentation reflects the new architecture.

* **Tasks:**  
  1. **Full System Test:** Execute the main `orchestrator.py` script to run a complete, end-to-end test of the entire content generation and publication workflow.  
  2. **Verification:** Manually verify that each step has completed successfully: the podcast appears in Spotify for Podcasters, the newsletter is scheduled in Mailchimp, the blog post is live, and social/community posts are published.  
  3. **Code Review:** Perform a final review of all code changes to catch any remaining issues.  
  4. **Update Documentation:** Edit the `Vibe Dev_ Agent Roles and Tools.md` and `README.md` files to reflect all changes, including the new `utils.py` module, updated API usage, and any changes to environment variables.

