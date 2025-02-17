# THIS BELOW IS ONLY THE EXCERCISE DESCRIPTION! MY NOTES AND DOCS CAN BE FOUND [▶️ HERE! ⬅️ ⚠️ *(click me)* ⚠️](https://github.com/gerryjekova/pavkata-python-scraper-idea/blob/main/Gerry.md)

# Advanced AI News Scraper – Developer Assignment

## 1. Project Overview

The goal of this project is to develop a Python-based API that accepts a URL as input and returns scraped content from a news/media website. The scraper must dynamically generate or retrieve extraction rules (in JSON format) for each domain and then extract the following media fields (if available):

- **Title**
- **Content**
- **Author**
- **Publish Date**
- **Language**
- **Categories** (multiple allowed)
- **Media Files**:
  - Images
  - Videos
  - Embeds

When extraction rules for a domain are missing, the system should use an AI-powered schema generator (leveraging Crawl4AI’s capabilities with LLMs) to create the necessary rules (using either XPath or CSS selectors). These rules should then be saved in a per-domain JSON file within the project structure for future use. Additionally, if the website’s structure changes and the scraper fails to extract data correctly, a failsafe retry mechanism should be in place to trigger regeneration of the extraction rules.

The final deliverable is a Python API that:
1. Receives scraping tasks (with a URL) via a POST endpoint.
2. Queues and processes the task asynchronously, returning a UUID task ID immediately.
3. Provides a GET endpoint to retrieve the scraping result based on the task ID.

The project will make use of the [Crawl4AI library](https://github.com/unclecode/crawl4ai) to handle the crawling, extraction, and LLM-driven schema generation.

---

## 2. Functional Requirements

### 2.1. API Endpoints

- **POST `/scrape`**
  - **Input:** JSON payload with at least:
    - `url`: The URL to scrape.
    - *(Optional)* Extra parameters (if needed) such as custom headers, etc.
  - **Output:** JSON response with a unique task ID (UUID).

- **GET `/scrape/{task_id}`**
  - **Input:** Task ID (UUID) as a URL parameter.
  - **Output:** JSON response with:
    - Current status of the task (e.g., queued, processing, completed, failed).
    - When completed, the extracted content in JSON format.

### 2.2. Scraping Logic

- **Extraction Rules:**
  - For a given domain (extracted from the URL), check if a JSON configuration file with extraction rules exists.
  - **If rules exist:**
    - Use them to configure the Crawl4AI extraction strategy.
  - **If rules are missing:**
    - Use Crawl4AI’s LLM-based automatic schema generation feature to analyze sample HTML from the website and generate extraction rules.
    - Save the generated rules in a JSON file named by domain (e.g., `configs/example.com.json`) for future runs.

- **Data Fields to Extract:**
  - Title
  - Content
  - Author
  - Publish Date
  - Language
  - Categories
  - Media Files (images, videos, embeds)

- **Domain-Specific Configuration:**
  - Each JSON configuration file should include:
    - Extraction rules (selectors using XPath or CSS).
    - Additional configuration options:
      - Whether to use a headless browser.
      - Whether to route requests through proxies.
      - Any other domain-specific settings (e.g., timeouts, user-agent strings).

- **Failsafe and Retry Mechanism:**
  - If a scraping attempt fails (e.g., extraction returns incomplete or no data due to structural changes), the system should:
    - Trigger a regeneration of the extraction schema using the LLM.
    - Optionally, retry the scraping process with the new rules.
  - Log the failure and subsequent recovery steps for debugging and monitoring.

### 2.3. Queue Management

- Implement a simple queue system to manage incoming scraping tasks.
- Each new task should:
  - Immediately return a UUID as a task ID.
  - Be processed asynchronously in the background.
- Ensure that tasks can be retried (in case of transient failures) and that their status can be queried via the GET endpoint.

---

## 3. Technical Requirements

- **Programming Language:** Python 3.8+
- **Framework:** Preferably FastAPI for building asynchronous HTTP endpoints.
- **Libraries/Tools:**
  - **Crawl4AI:** For crawling and extraction.
  - **Asyncio:** For asynchronous processing.
  - **Pydantic:** For data validation (if using FastAPI).
  - **UUID:** For generating task IDs.
  - **Any persistence/storage mechanism:** For storing task statuses/results and configuration files (this can be as simple as in-memory storage for a prototype or file-based for configs).

- **Coding Standards:**
  - Use clear module separation (e.g., API layer, scraper engine, task queue management, configuration management).
  - Write unit tests for critical components.
  - Use logging to track task flow, successes, and failures.

---

## 4. Detailed Task Breakdown

### Task 1: API Endpoint Setup

- **Objective:** Set up FastAPI (or another async framework) with two endpoints:
  - POST `/scrape` – To receive a new scraping task.
  - GET `/scrape/{task_id}` – To fetch the result/status of a scraping task.
- **Deliverable:** A basic API skeleton that handles requests and returns a task ID for new tasks.

### Task 2: Task Queue Management

- **Objective:** Implement a simple asynchronous queue to handle scraping tasks.
- **Requirements:**
  - On receiving a new task, add it to the queue.
  - Process tasks in the background.
  - Maintain task statuses (queued, processing, completed, failed).
- **Deliverable:** A module for queue management with proper status tracking.

### Task 3: Domain Configuration Management

- **Objective:** Develop a system to load/save JSON configuration files per domain.
- **Requirements:**
  - Check if a configuration file exists for a domain.
  - If not, later steps will generate it using AI.
  - Provide an API to read/write these configuration files.
- **Deliverable:** A configuration management module that handles domain-specific JSON files (e.g., stored in a `configs/` folder).

### Task 4: Integration with Crawl4AI

- **Objective:** Integrate Crawl4AI to perform the web crawling and extraction.
- **Requirements:**
  - Use Crawl4AI’s API to crawl a provided URL.
  - Configure the extraction strategy using rules loaded from the domain JSON file.
  - If rules are missing, call the LLM-based schema generator:
    - Use either OpenAI’s GPT-4 or Ollama as configured.
  - Extract the required fields (title, content, author, etc.).
- **Deliverable:** A scraping module that, given a URL and configuration, returns extracted JSON data.

### Task 5: Failsafe Retry Strategy

- **Objective:** Implement a failsafe mechanism to detect when scraping fails due to website structure changes.
- **Requirements:**
  - Detect when required fields are missing or extraction fails.
  - Automatically trigger regeneration of the extraction schema.
  - Retry scraping with the new schema.
  - Limit retries and log failures.
- **Deliverable:** Enhance the scraping module with error detection, schema regeneration, and retry logic.

### Task 6: API Response and Result Retrieval

- **Objective:** Combine all components so that when a scraping task is submitted, it is processed correctly and results are stored for retrieval.
- **Requirements:**
  - Upon task completion, store the results (or errors) with the corresponding task ID.
  - The GET endpoint should retrieve the current status and results if available.
- **Deliverable:** Full integration between the task queue, scraper, and API endpoints.

### Task 7: Testing & Documentation

- **Objective:** Write tests and documentation.
- **Requirements:**
  - Unit tests for:
    - API endpoints.
    - Task queue management.
    - Domain configuration loader/saver.
    - Scraping module and retry logic.
  - Document the code, usage, and how to add new domain configurations.
- **Deliverable:** A test suite and a README.md detailing setup instructions and usage.

---

## 5. Project Architecture Diagram

```
+---------------------+
|    API Endpoints    |
|  (FastAPI Service)  |
+----------+----------+
           |
           v
+---------------------+
|   Task Queue &      |
|   Manager Module    |
+----------+----------+
           |
           v
+---------------------+      +----------------------+
|   Scraping Module   |<---->| Domain Config Module |
| (Crawl4AI Wrapper)  |      | (Load/Save JSON)     |
+----------+----------+      +----------------------+
           |
           v
+---------------------+
|   Failsafe Retry    |
|   & AI Schema Gen   |
+---------------------+
```

---

## 6. Deliverables and Timeline

- **Week 1:**
  - Set up project structure and API endpoints.
  - Implement basic task queue management.
- **Week 2:**
  - Develop domain configuration management.
  - Integrate Crawl4AI for basic scraping.
- **Week 3:**
  - Implement LLM-based automatic schema generation.
  - Add failsafe retry strategy.
- **Week 4:**
  - End-to-end integration and testing.
  - Documentation and final code review.

---

## 7. Additional Notes

- **Error Handling:** Ensure robust error handling throughout. All errors (e.g., connectivity issues, invalid HTML, extraction failures) should be logged and reported via the API.
- **Extensibility:** Design the modules with extensibility in mind so that new fields or domain-specific tweaks can be added easily.
- **Performance:** While this is a prototype, consider using asynchronous operations wherever possible to avoid blocking the API, especially during crawling and schema generation.
