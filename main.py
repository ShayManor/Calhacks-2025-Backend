import requests, time, json, logging

logging.basicConfig(level=logging.INFO)


def bulk_create(prompts: list[str], base_url="http://localhost:5000"):
    """
    For each prompt in `prompts`, attempt to create an agent by calling
    /create_agent up to two times. If the server rejects POST with 405,
    fall back to GET?prompt=<...>, retry once on failure, then skip.
    Returns a dict mapping each prompt to the JSON response or None.
    """
    results: dict[str, dict | None] = {}

    for prompt in prompts:
        for attempt in (1, 2):
            try:
                # Try POST first
                url = f"{base_url}/create_agent"
                logging.info("Creating agent for prompt (attempt %d): %s", attempt, prompt[:50])
                resp = requests.post(
                    url,
                    json={"prompt": prompt},
                    timeout=420
                )
                if resp.status_code == 405:
                    # METHOD NOT ALLOWED: fall back to GET
                    logging.warning("POST returned 405, retrying with GET")
                    resp = requests.post(
                        url,
                        params={"prompt": prompt},
                        timeout=420
                    )

                resp.raise_for_status()  # HTTPError for 4xx/5xx

                # parse JSON
                data = resp.json()
                results[prompt] = data
                logging.info("✓ Success for prompt: %s (%.2fs)",
                             prompt[:40], resp.elapsed.total_seconds())
                break  # stop retrying on success

            except requests.HTTPError as he:
                logging.warning("HTTP error on attempt %d for '%s': %s",
                                attempt, prompt[:40], he)
            except requests.RequestException as re:
                logging.warning("Request exception on attempt %d for '%s': %s",
                                attempt, prompt[:40], re)
            except json.JSONDecodeError as je:
                logging.warning("Invalid JSON response on attempt %d for '%s': %s",
                                attempt, prompt[:40], je)
            except Exception as e:
                logging.warning("Unexpected error on attempt %d for '%s': %s",
                                attempt, prompt[:40], e)

            # on failure, record None if last attempt
            if attempt == 2:
                results[prompt] = None

            time.sleep(1)  # brief pause before retry
        time.sleep(10)
    return results


if __name__ == '__main__':
    prompts = [
        "Define the root agent “ResearchMaster” with the responsibility of orchestrating all sub-agents in a scholarly research pipeline.",
        "Under “ResearchMaster”, create a “Crawler” agent that collects research papers from multiple online scholarly databases.",
        "Under “Crawler”, create a “LinkParser” agent that parses each paper’s reference links and removes duplicates.",
        "Under “Crawler”, create a “ContentFetcher” agent that downloads HTML or PDF content for every parsed link.",
        "Under “ContentFetcher”, create a “CleanHTML” agent that sanitizes HTML and strips out scripts, ads, and navigation.",
        "Under “CleanHTML”, create a “TextExtractor” agent that extracts plain text from sanitized HTML fragments.",
        "Under “TextExtractor”, create a “LanguageDetector” agent that filters out non-English documents.",
        "Under “LanguageDetector”, create an “EnglishFilter” agent that retains only documents detected as English.",
        "Under “EnglishFilter”, create a “MetadataExtractor” agent that pulls titles, authors, dates, and journal info.",
        "Under “MetadataExtractor”, create a “CitationExtractor” agent that identifies in-text citations and bibliography entries.",
        "Under “CitationExtractor”, create a “Deduplicator” agent that merges multiple references to the same work.",
        "Under “Deduplicator”, create a “PDFDownloader” agent that retrieves PDF files for each unique citation.",
        "Under “PDFDownloader”, create a “PDFTextExtractor” agent that uses OCR or PDF parsing to extract raw text.",
        "Under “PDFTextExtractor”, create a “SectionSplitter” agent that breaks papers into Introduction, Methods, Results, etc.",
        "Under “SectionSplitter”, create an “AbstractExtractor” agent that isolates and stores each paper’s abstract.",
        "Under “AbstractExtractor”, create a “KeywordExtractor” agent that identifies the top 10 keywords per paper.",
        "Under “KeywordExtractor”, create a “TopicModeler” agent that clusters papers into thematic groups via LDA.",
        "Under “TopicModeler”, create a “ClusterLabeler” agent that assigns human-readable labels to each topic cluster.",
        "Under “ClusterLabeler”, create a “TrendDetector” agent that analyses publication dates to surface emerging topics.",
        "Under “TrendDetector”, create a “SentimentAnalysis” agent that gauges the tone of abstracts over time.",
        "Under “SentimentAnalysis”, create a “SummaryGenerator” agent that composes concise executive summaries of sentiment trends.",
        "Under “SummaryGenerator”, create an “ExecutiveBrief” agent that formats summaries into slide-ready bullet points.",
        "Under “ExecutiveBrief”, create a “ChartGenerator” agent that uses Matplotlib to draw trend charts.",
        "Under “ChartGenerator”, create a “ReportAssembler” agent that combines charts and text into a PDF report.",
        "Under “ReportAssembler”, create a “FormatMapper” agent that converts the PDF into HTML and Markdown versions.",
        "Under “FormatMapper”, create a “PDFReporter” agent that emails the final report to stakeholders.",
        "Under “PDFReporter”, create an “EmailNotifier” agent that sends success/failure notifications to a Slack channel.",
        "Under “ResearchMaster”, create an “Analyzer” agent that runs statistical and machine-learning models on extracted data.",
        "Under “Analyzer”, create a “RegressionModel” agent that fits predictive regressions on paper citation counts.",
        "Under “RegressionModel”, create a “PredictionAgent” that forecasts future citation trajectories per topic.",
        "Under “PredictionAgent”, create an “AnomalyDetector” agent that flags papers with unexpectedly rapid growth.",
        "Under “AnomalyDetector”, create an “OutlierLogger” agent that logs anomalous growth cases for review.",
        "Under “ResearchMaster”, create a “Summarizer” agent that generates high-level summaries of analysis results.",
        "Under “Summarizer”, create an “AbstractBrief” agent that shortens full-paper summaries into three sentences.",
        "Under “AbstractBrief”, create a “PlainLanguage” agent that rewrites summaries at an 8th-grade reading level.",
        "Under “ResearchMaster”, create an “InteractiveQA” agent that answers user questions about the research dataset.",
        "Under “InteractiveQA”, create a “ContextLoader” agent that fetches relevant document snippets on demand.",
        "Under “ContextLoader”, create a “MemoryManager” agent that caches recent queries and results per session.",
        "Under “MemoryManager”, create a “SessionTracker” agent that preserves user-agent conversation states.",
        "Under “SessionTracker”, create a “HistoryReconstructor” agent that rebuilds past Q&A context from logs.",
        "Under “ResearchMaster”, create a “QueryRouter” agent that directs user prompts to the appropriate sub-agent.",
        "Under “QueryRouter”, create a “DSLTranslator” agent that converts user questions into structured API calls.",
        "Under “DSLTranslator”, create a “SQLGenerator” agent that generates SQL queries for the data warehouse.",
        "Under “SQLGenerator”, create a “DatabaseQuery” agent that executes queries against your analytics database.",
        "Under “ResearchMaster”, create a “DataVisualizer” agent that turns query results into charts and graphs.",
        "Under “DataVisualizer”, create a “PlotGenerator” agent that produces interactive D3.js visualizations.",
        "Under “PlotGenerator”, create a “DashboardUpdater” agent that publishes visuals to a live web dashboard.",
        "Under “ResearchMaster”, create a “Notifier” agent that alerts users when new insights are available.",
        "Under “Notifier”, create a “SlackNotifier” agent that posts messages to a configured Slack channel.",
        "Under “Notifier”, create an “EmailNotifier” agent that emails users with summary attachments.",
        "Under “ResearchMaster”, create a “Scheduler” agent that orchestrates daily or weekly runs of the pipeline.",
        "Under “Scheduler”, create a “CronManager” agent that converts human-friendly schedules into cron expressions.",
        "Under “CronManager”, create a “TaskDispatcher” agent that triggers the `/prompt` route at scheduled times.",
        "Under “TaskDispatcher”, create a “LoadBalancer” agent that distributes workload across multiple containers.",
        "Under “ResearchMaster”, create a “ResourceMonitor” agent that tracks CPU, memory, and disk usage of all sub-agents.",
        "Under “ResourceMonitor”, create a “HealthChecker” agent that performs periodic health-check pings on each service.",
        "Under “HealthChecker”, create an “AlertGenerator” agent that creates PagerDuty alerts on failures.",
        "Under “HealthChecker”, create a “RestartManager” agent that attempts to restart failed sub-agents automatically.",
        "Under “ResearchMaster”, create an “Archive” agent that backs up raw data and reports to long-term storage.",
        "Under “Archive”, create an “S3Uploader” agent that uploads backups to AWS S3 with versioning enabled.",
        "Under “Archive”, create a “GDriveUploader” agent that also mirrors backups to Google Drive folders.",
        "Under “ResearchMaster”, create a “Security” agent that enforces API key and role-based access controls.",
        "Under “Security”, create an “AccessController” agent that validates JWT tokens on each request.",
        "Under “AccessController”, create an “AuditLogger” agent that logs every sensitive operation.",
        "Under “ResearchMaster”, create a “ConfigManager” agent that centralizes all configuration parameters.",
        "Under “ConfigManager”, create a “VersionControl” agent that snapshots configuration in Git commits.",
        "Under “VersionControl”, create a “DiffAnalyzer” agent that highlights config drifts between runs.",
        "Under “ResearchMaster”, create a “Benchmark” agent that measures end-to-end latency of each pipeline.",
        "Under “Benchmark”, create a “PerformanceTester” agent that simulates high-load scenarios.",
        "Under “PerformanceTester”, create a “LoadTester” agent that ramps up concurrent requests to measure throughput.",
        "Under “ResearchMaster”, create a “FeedbackCollector” agent that gathers user feedback after each run.",
        "Under “FeedbackCollector”, create a “SurveyAdmin” agent that sends out automated satisfaction surveys.",
        "Under “ResearchMaster”, create a “Documentation” agent that auto-generates README and API docs.",
        "Under “Documentation”, create a “MarkdownGenerator” agent that converts docstrings into Markdown files.",
        "Under “MarkdownGenerator”, create an “HTMLDocBuilder” agent that publishes docs as a static site.",
        "Under “ResearchMaster”, create a “Deployment” agent that handles rolling updates to all sub-agents.",
        "Under “Deployment”, create a “DockerBuilder” agent that builds and tags Docker images for each service.",
        "Under “DockerBuilder”, create an “ImagePublisher” agent that pushes images to a container registry.",
        "Under “ResearchMaster”, create an “Integration” agent that runs end-to-end integration tests.",
        "Under “Integration”, create an “APIValidator” agent that verifies each endpoint’s contract against OpenAPI specs.",
        "Under “APIValidator”, create a “ContractTester” agent that fails builds on spec violations.",
        "Under “ResearchMaster”, create a “Cleanup” agent that prunes old logs, temp files, and database partitions.",
        "Under “Cleanup”, create a “TempFileRemover” agent that deletes files older than 7 days.",
        "Under “ResearchMaster”, create a “Metrics” agent that aggregates usage metrics across all agents.",
        "Under “Metrics”, create a “UsageTracker” agent that records request counts, latencies, and error rates.",
        "Under “UsageTracker”, create a “BillingReporter” agent that summarizes usage costs per agent.",
        "Under “ResearchMaster”, create an “AITrainer” agent that runs model training pipelines on collected data.",
        "Under “AITrainer”, create a “ModelSelector” agent that picks the best performing model architecture.",
        "Under “ModelSelector”, create a “HyperparamTuner” agent that optimizes hyperparameters via Bayesian search.",
        "Under “HyperparamTuner”, create a “TrainingMonitor” agent that logs GPU utilization and loss curves.",
        "Under “ResearchMaster”, create an “NLP” agent that handles all natural-language processing tasks.",
        "Under “NLP”, create a “Tokenizer” agent that tokenizes raw text into subwords for embedding generation.",
        "Under “Tokenizer”, create an “EmbeddingBuilder” agent that generates vector embeddings using a transformer model.",
        "Under “EmbeddingBuilder”, create a “SimilaritySearch” agent that finds semantically similar papers.",
        "Under “ResearchMaster”, create a “GenAgentFactory” agent that dynamically spawns new specialized agents.",
        "Under “GenAgentFactory”, create a “CodeGenerator” agent that writes boilerplate code for new micro-agents.",
        "Under “CodeGenerator”, create a “TestGenerator” agent that writes pytest tests for newly generated code.",
        "Under “TestGenerator”, create a “CoverageAnalyzer” agent that measures test coverage and reports gaps.",
        "Under “CoverageAnalyzer”, create a “ReportNotifier” agent that emails a coverage summary after CI runs."
    ]

    responses = bulk_create(prompts[:1], base_url="http://127.0.0.1:5000")
    with open('data.json', 'w') as f:
        f.writelines(json.dumps(responses[:1], indent=2))
    print(json.dumps(responses, indent=2))
