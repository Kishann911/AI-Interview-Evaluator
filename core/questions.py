import random
from typing import Optional

# ── Question bank ─────────────────────────────────────────────────────────────
# Structure: QUESTIONS[domain] = [list of question dicts]
# Each question: id, question, difficulty, topic, expected_keywords, follow_up

QUESTIONS: dict[str, list[dict]] = {

    # =========================================================================
    "Software Engineering": [
        # ── Easy ─────────────────────────────────────────────────────────────
        {
            "id": 1,
            "question": "What are the four pillars of Object-Oriented Programming? Briefly explain each one.",
            "difficulty": "Easy",
            "topic": "OOP",
            "expected_keywords": [
                "encapsulation", "inheritance", "polymorphism", "abstraction",
                "hiding", "reuse", "interface", "override",
            ],
            "follow_up": "Can you give a real-world analogy for each pillar?",
        },
        {
            "id": 2,
            "question": "What is the difference between an array and a linked list? When would you choose one over the other?",
            "difficulty": "Easy",
            "topic": "Data Structures",
            "expected_keywords": [
                "contiguous", "random access", "O(1)", "O(n)", "pointer",
                "insertion", "deletion", "cache", "dynamic size",
            ],
            "follow_up": "How does a doubly-linked list differ from a singly-linked list, and when is it preferable?",
        },
        {
            "id": 3,
            "question": "Explain Big-O notation. What does O(n log n) mean, and which common sorting algorithm runs at that complexity?",
            "difficulty": "Easy",
            "topic": "Algorithms",
            "expected_keywords": [
                "worst case", "time complexity", "space complexity", "logarithmic",
                "merge sort", "quicksort", "heapsort", "scalability",
            ],
            "follow_up": "What is the difference between O(n log n) and O(n²) in practice for n = 1,000,000?",
        },
        {
            "id": 4,
            "question": "What is the difference between `git merge` and `git rebase`? When should you use each?",
            "difficulty": "Easy",
            "topic": "Version Control",
            "expected_keywords": [
                "merge commit", "linear history", "rewrite", "public branch",
                "fast-forward", "conflict", "feature branch", "main",
            ],
            "follow_up": "What does `git rebase -i` allow you to do, and why is it useful before opening a pull request?",
        },
        {
            "id": 5,
            "question": "What are the core constraints that make an API RESTful? Name and explain at least four.",
            "difficulty": "Easy",
            "topic": "REST APIs",
            "expected_keywords": [
                "stateless", "client-server", "uniform interface", "cacheable",
                "layered", "HTTP methods", "resource", "URI",
            ],
            "follow_up": "What is HATEOAS, and is it required for an API to be considered truly RESTful?",
        },
        # ── Medium ────────────────────────────────────────────────────────────
        {
            "id": 6,
            "question": "Explain polymorphism with a concrete code-level example. What is the difference between compile-time and runtime polymorphism?",
            "difficulty": "Medium",
            "topic": "OOP",
            "expected_keywords": [
                "method overriding", "method overloading", "virtual", "interface",
                "dynamic dispatch", "compile-time", "runtime", "subclass",
            ],
            "follow_up": "How does polymorphism support the Open/Closed Principle from SOLID?",
        },
        {
            "id": 7,
            "question": "How does a hash map work internally? What is a hash collision, and how do chaining and open addressing resolve it?",
            "difficulty": "Medium",
            "topic": "Data Structures",
            "expected_keywords": [
                "hash function", "bucket", "collision", "chaining", "open addressing",
                "load factor", "rehashing", "O(1)", "worst case O(n)",
            ],
            "follow_up": "How does a hash map's load factor affect its performance, and when does resizing typically occur?",
        },
        {
            "id": 8,
            "question": "Explain how quicksort works. What is its average and worst-case time complexity, and how can you avoid the worst case?",
            "difficulty": "Medium",
            "topic": "Algorithms",
            "expected_keywords": [
                "pivot", "partition", "divide and conquer", "O(n log n)", "O(n²)",
                "random pivot", "median of three", "in-place", "stack overflow",
            ],
            "follow_up": "In what scenarios would you prefer merge sort over quicksort despite both being O(n log n) average?",
        },
        {
            "id": 9,
            "question": "Explain the Singleton design pattern. How do you implement a thread-safe Singleton in a multi-threaded environment?",
            "difficulty": "Medium",
            "topic": "Design Patterns",
            "expected_keywords": [
                "single instance", "private constructor", "static", "thread-safe",
                "double-checked locking", "synchronized", "lazy initialization", "eager",
            ],
            "follow_up": "What are the downsides of the Singleton pattern, and when is it considered an anti-pattern?",
        },
        {
            "id": 10,
            "question": "Explain the Open/Closed Principle from SOLID. Give a concrete example of code that violates it and show how to fix it.",
            "difficulty": "Medium",
            "topic": "SOLID Principles",
            "expected_keywords": [
                "open for extension", "closed for modification", "abstract", "interface",
                "strategy pattern", "if-else chain", "polymorphism", "inheritance",
            ],
            "follow_up": "How does the Open/Closed Principle relate to the Strategy design pattern?",
        },
        {
            "id": 11,
            "question": "What is the difference between unit, integration, and end-to-end tests? What is the testing pyramid, and why does it matter?",
            "difficulty": "Medium",
            "topic": "Testing Strategies",
            "expected_keywords": [
                "unit test", "integration test", "E2E", "mock", "stub",
                "testing pyramid", "speed", "isolation", "coverage", "confidence",
            ],
            "follow_up": "When is it acceptable to skip unit tests in favor of integration tests?",
        },
        # ── Hard ──────────────────────────────────────────────────────────────
        {
            "id": 12,
            "question": "Explain dynamic programming. How do you identify when to apply it, and what is the difference between memoization and tabulation?",
            "difficulty": "Hard",
            "topic": "Algorithms",
            "expected_keywords": [
                "overlapping subproblems", "optimal substructure", "memoization",
                "tabulation", "top-down", "bottom-up", "recurrence", "Fibonacci", "knapsack",
            ],
            "follow_up": "Walk me through how you would solve the 0/1 Knapsack problem using dynamic programming.",
        },
        {
            "id": 13,
            "question": "What are the trade-offs between a microservices architecture and a monolith? Under what conditions should you choose each?",
            "difficulty": "Hard",
            "topic": "Microservices",
            "expected_keywords": [
                "independently deployable", "scaling", "distributed systems", "latency",
                "data consistency", "team autonomy", "operational complexity", "Conway's Law",
                "service mesh", "monolith first",
            ],
            "follow_up": "How would you decompose a monolith into microservices incrementally without a full rewrite?",
        },
        {
            "id": 14,
            "question": "Explain the Observer design pattern. Describe its structure, a real-world use case, and potential pitfalls.",
            "difficulty": "Hard",
            "topic": "Design Patterns",
            "expected_keywords": [
                "subject", "observer", "subscribe", "publish", "notify",
                "event-driven", "loose coupling", "memory leak", "event bus", "MVC",
            ],
            "follow_up": "How does the Observer pattern differ from the Pub/Sub pattern, and when would you prefer one over the other?",
        },
        {
            "id": 15,
            "question": "Walk me through your systematic approach to debugging a production incident where a service is returning 500 errors for 10% of requests.",
            "difficulty": "Hard",
            "topic": "Debugging",
            "expected_keywords": [
                "logs", "metrics", "tracing", "reproduce", "hypothesis",
                "rollback", "canary", "percentile", "correlation", "post-mortem",
            ],
            "follow_up": "How do you prevent the same class of bugs from recurring after resolving the incident?",
        },
    ],

    # =========================================================================
    "HR / Behavioral": [
        # ── Easy ─────────────────────────────────────────────────────────────
        {
            "id": 16,
            "question": "Tell me about yourself. Walk me through your background and what brings you here today.",
            "difficulty": "Easy",
            "topic": "Self-Introduction",
            "expected_keywords": [
                "current role", "experience", "skills", "career journey",
                "motivated", "relevant", "concise", "forward-looking",
            ],
            "follow_up": "What's the single professional achievement you're most proud of from your background?",
        },
        {
            "id": 17,
            "question": "What is your greatest professional strength, and can you give a specific example of when it made a measurable difference?",
            "difficulty": "Easy",
            "topic": "Strengths",
            "expected_keywords": [
                "STAR", "situation", "task", "action", "result",
                "quantifiable", "relevant", "genuine", "impact",
            ],
            "follow_up": "How have you deliberately developed this strength further over the past year?",
        },
        {
            "id": 18,
            "question": "What is your greatest professional weakness, and what concrete steps have you taken to improve it?",
            "difficulty": "Easy",
            "topic": "Weaknesses",
            "expected_keywords": [
                "self-aware", "genuine", "growth", "action", "progress",
                "learning", "not a strength reframed", "development",
            ],
            "follow_up": "Can you give an example of a situation where this weakness affected your work and what you did in response?",
        },
        {
            "id": 19,
            "question": "Why do you want to work at this company specifically? What drew you to this role?",
            "difficulty": "Easy",
            "topic": "Company Motivation",
            "expected_keywords": [
                "research", "mission", "product", "culture", "values",
                "career alignment", "specific", "genuine", "contribution",
            ],
            "follow_up": "What do you know about our recent product launches or company direction that excites you?",
        },
        {
            "id": 20,
            "question": "Where do you see yourself professionally in five years?",
            "difficulty": "Easy",
            "topic": "Career Goals",
            "expected_keywords": [
                "growth", "skills", "leadership", "impact", "realistic",
                "aligned", "ambition", "learning", "contribution",
            ],
            "follow_up": "What specific steps are you taking right now to move toward that goal?",
        },
        # ── Medium ────────────────────────────────────────────────────────────
        {
            "id": 21,
            "question": "Tell me about a specific time you had a conflict with a coworker. How did you handle it, and what was the outcome?",
            "difficulty": "Medium",
            "topic": "Conflict Resolution",
            "expected_keywords": [
                "listen", "empathy", "direct", "private", "compromise",
                "resolution", "relationship", "outcome", "professional", "learned",
            ],
            "follow_up": "Looking back, would you handle it differently now? What did you learn about conflict resolution?",
        },
        {
            "id": 22,
            "question": "Describe a situation where you had to lead a team through a challenging project. What was your approach and what did you learn about leadership?",
            "difficulty": "Medium",
            "topic": "Team Leadership",
            "expected_keywords": [
                "delegate", "communicate", "align", "motivate", "accountability",
                "decision", "obstacles", "cross-functional", "outcome", "retrospective",
            ],
            "follow_up": "How do you adapt your leadership style when team members have very different working preferences?",
        },
        {
            "id": 23,
            "question": "Tell me about a significant professional failure. What happened, what was your role, and what did you do next?",
            "difficulty": "Medium",
            "topic": "Handling Failure",
            "expected_keywords": [
                "accountability", "honest", "root cause", "learned", "action",
                "prevent recurrence", "growth", "resilience", "team", "transparency",
            ],
            "follow_up": "How did this failure change the way you approach similar situations today?",
        },
        {
            "id": 24,
            "question": "Describe a time when you were working under significant pressure or a tight deadline. How did you manage it?",
            "difficulty": "Medium",
            "topic": "Working Under Pressure",
            "expected_keywords": [
                "prioritize", "communicate", "focus", "trade-offs", "calm",
                "stakeholders", "quality", "delegate", "delivered", "stress management",
            ],
            "follow_up": "What systems or habits do you maintain proactively to avoid chronic pressure situations?",
        },
        {
            "id": 25,
            "question": "What is your biggest professional achievement to date? Why was it significant, and what was your specific contribution?",
            "difficulty": "Medium",
            "topic": "Biggest Achievement",
            "expected_keywords": [
                "impact", "quantify", "ownership", "collaboration", "challenge",
                "result", "recognized", "proud", "specific", "stakeholders",
            ],
            "follow_up": "If you could do that project over again, what would you do differently to make the outcome even stronger?",
        },
        {
            "id": 26,
            "question": "How do you manage your time and priorities when you have several high-stakes tasks competing for your attention simultaneously?",
            "difficulty": "Medium",
            "topic": "Time Management",
            "expected_keywords": [
                "prioritize", "urgent vs important", "Eisenhower", "delegate",
                "communicate", "trade-offs", "system", "deadlines", "focus", "block",
            ],
            "follow_up": "Describe a specific situation where your time management system was put to the test.",
        },
        # ── Hard ──────────────────────────────────────────────────────────────
        {
            "id": 27,
            "question": "Tell me about a time you had to work closely with someone whose work style or personality was very different from yours. How did you make it work?",
            "difficulty": "Hard",
            "topic": "Difficult Colleague",
            "expected_keywords": [
                "understand", "empathy", "adapt", "communication style",
                "find common ground", "respect", "outcome", "professional", "bridge",
            ],
            "follow_up": "What did that experience teach you about building effective working relationships with diverse personalities?",
        },
        {
            "id": 28,
            "question": "Describe a time when you received criticism or negative feedback that you initially disagreed with. How did you respond?",
            "difficulty": "Hard",
            "topic": "Handling Criticism",
            "expected_keywords": [
                "listen", "open-minded", "self-reflect", "separate ego",
                "clarify", "growth mindset", "action", "changed behavior", "outcome",
            ],
            "follow_up": "How do you now proactively seek out feedback rather than waiting for it to be given?",
        },
        {
            "id": 29,
            "question": "Tell me about a time you had to adapt to a major change at work — a restructure, new technology, or shift in strategy — that you didn't agree with. How did you handle it?",
            "difficulty": "Hard",
            "topic": "Adapting to Change",
            "expected_keywords": [
                "understand why", "express concern appropriately", "commit",
                "flexible", "ambiguity", "positive attitude", "resilience", "outcome",
            ],
            "follow_up": "How do you help others on your team adapt to change when they are resistant?",
        },
        {
            "id": 30,
            "question": "Tell me about a time you identified and solved a significant problem entirely on your own initiative, without being asked.",
            "difficulty": "Hard",
            "topic": "Initiative",
            "expected_keywords": [
                "proactive", "ownership", "spotted", "business impact",
                "built coalition", "executed", "result", "no permission needed", "stakeholders",
            ],
            "follow_up": "How do you balance taking initiative with not overstepping or duplicating work others are doing?",
        },
    ],

    # =========================================================================
    "System Design": [
        # ── Easy ─────────────────────────────────────────────────────────────
        {
            "id": 31,
            "question": "What is load balancing? Explain at least three common load balancing algorithms and their trade-offs.",
            "difficulty": "Easy",
            "topic": "Load Balancing",
            "expected_keywords": [
                "round robin", "least connections", "IP hash", "weighted",
                "health check", "sticky sessions", "L4", "L7", "availability",
            ],
            "follow_up": "What is the difference between L4 and L7 load balancing, and when would you use each?",
        },
        {
            "id": 32,
            "question": "What is a CDN (Content Delivery Network)? How does it work, and what types of content benefit most from it?",
            "difficulty": "Easy",
            "topic": "CDN Design",
            "expected_keywords": [
                "edge", "PoP", "cache", "latency", "origin server",
                "static assets", "Anycast", "TTL", "invalidation", "DDoS",
            ],
            "follow_up": "How would you handle cache invalidation on a CDN when you need to push urgent content updates?",
        },
        {
            "id": 33,
            "question": "Explain the CAP theorem. Given that network partitions are unavoidable, what real choice does the theorem leave us with?",
            "difficulty": "Easy",
            "topic": "CAP Theorem",
            "expected_keywords": [
                "consistency", "availability", "partition tolerance", "CP", "AP",
                "eventual consistency", "strong consistency", "trade-off", "Cassandra", "HBase",
            ],
            "follow_up": "How does the PACELC model extend CAP theorem, and why is it considered more realistic?",
        },
        {
            "id": 34,
            "question": "What is database sharding? Explain horizontal vs vertical sharding and two common sharding strategies.",
            "difficulty": "Easy",
            "topic": "Database Sharding",
            "expected_keywords": [
                "shard key", "horizontal", "vertical", "hash-based", "range-based",
                "hot shard", "resharding", "cross-shard join", "replication",
            ],
            "follow_up": "What problems arise when a shard key is chosen poorly, and how would you mitigate hot-shard issues?",
        },
        {
            "id": 35,
            "question": "What is rate limiting, and why is it critical in public APIs? Describe two common rate limiting algorithms.",
            "difficulty": "Easy",
            "topic": "Rate Limiting",
            "expected_keywords": [
                "token bucket", "sliding window", "fixed window", "leaky bucket",
                "throttle", "abuse", "DDoS", "per-user", "Redis", "429",
            ],
            "follow_up": "How would you implement distributed rate limiting when your API runs across 50 servers?",
        },
        # ── Medium ────────────────────────────────────────────────────────────
        {
            "id": 36,
            "question": "Design a URL shortener like bit.ly. Cover key generation, redirection, storage, and how you would scale to 100M URLs.",
            "difficulty": "Medium",
            "topic": "URL Shortener",
            "expected_keywords": [
                "base62", "hash", "collision", "Redis cache", "301 vs 302",
                "database", "sharding", "analytics", "custom alias", "expiry",
            ],
            "follow_up": "How would you add click analytics (geographic breakdown, referrer tracking) without slowing down redirects?",
        },
        {
            "id": 37,
            "question": "Design a distributed caching system like Redis. How does it handle replication, persistence, and eviction?",
            "difficulty": "Medium",
            "topic": "Distributed Cache",
            "expected_keywords": [
                "master-replica", "sentinel", "cluster", "LRU", "TTL",
                "AOF", "RDB snapshot", "eviction policy", "cache-aside", "write-through",
            ],
            "follow_up": "What is cache stampede (thundering herd) and how would you prevent it in a high-traffic system?",
        },
        {
            "id": 38,
            "question": "Explain consistent hashing. Why is it preferred over simple modulo hashing in distributed systems, and what is a virtual node?",
            "difficulty": "Medium",
            "topic": "Consistent Hashing",
            "expected_keywords": [
                "ring", "hash space", "virtual node", "node addition", "node removal",
                "minimal remapping", "modulo", "hotspot", "load distribution",
            ],
            "follow_up": "How do virtual nodes in consistent hashing improve load distribution when nodes have different capacities?",
        },
        {
            "id": 39,
            "question": "Design a notification system that supports push, email, and SMS for 50 million users. Focus on reliability and scale.",
            "difficulty": "Medium",
            "topic": "Notification System",
            "expected_keywords": [
                "message queue", "Kafka", "fan-out", "priority queue", "idempotency",
                "retry", "dead letter queue", "APNs", "FCM", "user preferences",
            ],
            "follow_up": "How would you ensure a notification is delivered exactly once, even if your worker crashes mid-send?",
        },
        {
            "id": 40,
            "question": "Design Instagram's news feed. How do you decide between fan-out on write vs fan-out on read, and what is the hybrid approach?",
            "difficulty": "Medium",
            "topic": "Social Feed",
            "expected_keywords": [
                "fan-out on write", "fan-out on read", "celebrity problem",
                "Redis sorted set", "timeline cache", "Cassandra", "follower graph",
                "ranking", "chronological", "hybrid",
            ],
            "follow_up": "How would you add algorithmic ranking (engagement prediction) to the feed without impacting read latency?",
        },
        # ── Hard ──────────────────────────────────────────────────────────────
        {
            "id": 41,
            "question": "Design Twitter/X's home timeline at scale. Walk through data modeling, write path, read path, and how you handle celebrity accounts.",
            "difficulty": "Hard",
            "topic": "Twitter Feed",
            "expected_keywords": [
                "fan-out", "Redis", "Cassandra", "tweet store", "follower list",
                "celebrity threshold", "pull on read", "push on write", "sharding", "replication",
            ],
            "follow_up": "Twitter recently moved from a fan-out-on-write to a fan-out-on-read approach for celebrity accounts. What are the implications of that change?",
        },
        {
            "id": 42,
            "question": "Design WhatsApp's real-time 1-on-1 and group messaging system. Cover message delivery, ordering, and the online/offline challenge.",
            "difficulty": "Hard",
            "topic": "Messaging System",
            "expected_keywords": [
                "WebSocket", "message queue", "delivery receipt", "ordering",
                "group fan-out", "offline storage", "end-to-end encryption",
                "connection server", "Zookeeper", "message ID",
            ],
            "follow_up": "How would you implement the 'message seen by all members' receipt for a group with 256 members efficiently?",
        },
        {
            "id": 43,
            "question": "Design Netflix's video streaming service. Cover upload pipeline, encoding, storage, CDN delivery, and adaptive bitrate streaming.",
            "difficulty": "Hard",
            "topic": "Streaming Platform",
            "expected_keywords": [
                "transcoding", "adaptive bitrate", "HLS", "DASH", "CDN",
                "S3", "chunked", "metadata service", "recommendation", "edge cache",
            ],
            "follow_up": "How does Netflix decide which CDN edge server to serve video from, and what metrics determine that routing decision?",
        },
        {
            "id": 44,
            "question": "Design Uber's ride-matching system. Focus on real-time driver location tracking, matching algorithm, and geospatial indexing.",
            "difficulty": "Hard",
            "topic": "Ride-Sharing",
            "expected_keywords": [
                "geospatial", "geohash", "Redis GEO", "WebSocket", "matching",
                "ETA", "supply-demand", "surge pricing", "driver state", "trip lifecycle",
            ],
            "follow_up": "How would you design the surge pricing engine to react to supply-demand imbalances in near-real-time?",
        },
        {
            "id": 45,
            "question": "Design Google Search's indexing and query pipeline at a high level. How does crawling, indexing, ranking, and serving work together?",
            "difficulty": "Hard",
            "topic": "Search Engine",
            "expected_keywords": [
                "web crawler", "inverted index", "PageRank", "ranking signals",
                "Bigtable", "MapReduce", "query parsing", "sharding", "serving layer", "cache",
            ],
            "follow_up": "How would you design the query auto-complete feature (search suggestions) to return results in under 100ms?",
        },
    ],

    # =========================================================================
    "Data Science & ML": [
        # ── Easy ─────────────────────────────────────────────────────────────
        {
            "id": 46,
            "question": "What is the difference between a classification problem and a regression problem? Give an example of each.",
            "difficulty": "Easy",
            "topic": "Classification vs Regression",
            "expected_keywords": [
                "discrete", "continuous", "label", "output", "logistic regression",
                "linear regression", "categorical", "probability", "threshold",
            ],
            "follow_up": "Can logistic regression be used for multi-class classification? If so, how?",
        },
        {
            "id": 47,
            "question": "What is overfitting? How do you detect it, and name four techniques to prevent it?",
            "difficulty": "Easy",
            "topic": "Overfitting",
            "expected_keywords": [
                "training accuracy", "validation accuracy", "gap", "regularization",
                "dropout", "early stopping", "more data", "cross-validation", "noise",
            ],
            "follow_up": "How is underfitting different from overfitting, and what does each tell you about model complexity?",
        },
        {
            "id": 48,
            "question": "Explain precision, recall, and F1 score. When would you optimize for precision over recall, and vice versa?",
            "difficulty": "Easy",
            "topic": "Evaluation Metrics",
            "expected_keywords": [
                "true positive", "false positive", "false negative", "precision",
                "recall", "F1", "harmonic mean", "imbalanced", "cancer detection", "spam",
            ],
            "follow_up": "What is the ROC-AUC score, and why is it often preferred over accuracy for imbalanced datasets?",
        },
        {
            "id": 49,
            "question": "What is feature engineering? Give three examples of feature transformations that can significantly improve model performance.",
            "difficulty": "Easy",
            "topic": "Feature Engineering",
            "expected_keywords": [
                "normalization", "encoding", "log transform", "interaction terms",
                "binning", "polynomial", "date extraction", "embedding", "domain knowledge",
            ],
            "follow_up": "How do you decide which features to include or exclude, and what tools help with feature selection?",
        },
        {
            "id": 50,
            "question": "How do you handle missing data in a machine learning dataset? Describe at least four strategies and when each is appropriate.",
            "difficulty": "Easy",
            "topic": "Missing Data",
            "expected_keywords": [
                "imputation", "mean", "median", "KNN imputation", "MICE",
                "drop rows", "indicator variable", "MCAR", "MAR", "MNAR",
            ],
            "follow_up": "Why is it important to fit imputation on the training set only and then apply it to the test set?",
        },
        # ── Medium ────────────────────────────────────────────────────────────
        {
            "id": 51,
            "question": "Explain the bias-variance tradeoff. How does model complexity affect each, and how do you find the sweet spot?",
            "difficulty": "Medium",
            "topic": "Bias-Variance Tradeoff",
            "expected_keywords": [
                "bias", "variance", "underfitting", "overfitting", "irreducible error",
                "model complexity", "regularization", "ensemble", "cross-validation",
            ],
            "follow_up": "How does bagging reduce variance without changing bias, and how does boosting reduce bias?",
        },
        {
            "id": 52,
            "question": "Explain K-fold cross-validation. Why is it better than a single train/test split, and what is stratified K-fold?",
            "difficulty": "Medium",
            "topic": "Cross-Validation",
            "expected_keywords": [
                "K folds", "holdout", "variance in estimate", "stratified",
                "class distribution", "time series", "LOOCV", "nested CV", "data leakage",
            ],
            "follow_up": "When using K-fold cross-validation for hyperparameter tuning, how do you avoid optimistic bias in the final reported score?",
        },
        {
            "id": 53,
            "question": "Compare decision trees and random forests. Why do random forests outperform individual trees, and what trade-offs do they introduce?",
            "difficulty": "Medium",
            "topic": "Decision Trees vs Random Forests",
            "expected_keywords": [
                "bagging", "bootstrap", "feature subset", "variance reduction",
                "interpretability", "ensemble", "depth", "Gini", "overfitting", "parallel",
            ],
            "follow_up": "What is feature importance in a random forest, and how is it computed? What are its known biases?",
        },
        {
            "id": 54,
            "question": "Explain gradient boosting. How does it differ from bagging, and why does XGBoost often win tabular ML competitions?",
            "difficulty": "Medium",
            "topic": "Gradient Boosting",
            "expected_keywords": [
                "sequential", "residuals", "weak learner", "learning rate",
                "regularization", "XGBoost", "LightGBM", "shrinkage", "early stopping", "trees",
            ],
            "follow_up": "What is the role of the learning rate (shrinkage) in gradient boosting, and how does it interact with the number of trees?",
        },
        {
            "id": 55,
            "question": "What is PCA (Principal Component Analysis)? When would you use it, and what are its limitations?",
            "difficulty": "Medium",
            "topic": "Dimensionality Reduction",
            "expected_keywords": [
                "variance", "eigenvalue", "eigenvector", "orthogonal", "curse of dimensionality",
                "linear", "interpretability", "standardize", "explained variance", "t-SNE",
            ],
            "follow_up": "How does t-SNE differ from PCA in its goal, and why is t-SNE not suitable for dimensionality reduction before training a model?",
        },
        {
            "id": 56,
            "question": "How do you design and evaluate an A/B test for a machine learning model change in production? What pitfalls should you watch for?",
            "difficulty": "Medium",
            "topic": "A/B Testing",
            "expected_keywords": [
                "control", "treatment", "statistical significance", "power", "sample size",
                "p-value", "novelty effect", "SRM", "metric", "guardrail metric",
            ],
            "follow_up": "What is a sample ratio mismatch (SRM), how do you detect it, and why does it invalidate an A/B test?",
        },
        # ── Hard ──────────────────────────────────────────────────────────────
        {
            "id": 57,
            "question": "Explain backpropagation in a neural network. How does the chain rule compute gradients, and what is the vanishing gradient problem?",
            "difficulty": "Hard",
            "topic": "Neural Networks",
            "expected_keywords": [
                "chain rule", "gradient", "loss", "weight update", "activation",
                "sigmoid", "vanishing gradient", "ReLU", "BatchNorm", "residual connections",
            ],
            "follow_up": "How do residual connections (skip connections) in ResNet specifically address the vanishing gradient problem?",
        },
        {
            "id": 58,
            "question": "When would you use a CNN vs an RNN for a machine learning problem? What architectural properties make each suited to its domain?",
            "difficulty": "Hard",
            "topic": "CNN vs RNN",
            "expected_keywords": [
                "spatial", "temporal", "convolutional filter", "pooling", "translation invariance",
                "sequence", "LSTM", "GRU", "attention", "Transformer", "local vs global",
            ],
            "follow_up": "Transformers have largely replaced RNNs for NLP tasks. What architectural property of Transformers gives them an advantage over LSTMs for long sequences?",
        },
        {
            "id": 59,
            "question": "Explain word embeddings. How are Word2Vec embeddings trained, and what is their key limitation that contextual embeddings (BERT) address?",
            "difficulty": "Hard",
            "topic": "NLP Basics",
            "expected_keywords": [
                "dense vector", "semantic similarity", "skip-gram", "CBOW",
                "negative sampling", "context window", "static embedding", "polysemy",
                "BERT", "contextual", "transformer",
            ],
            "follow_up": "How would you evaluate the quality of word embeddings, and what downstream tasks would you use as benchmarks?",
        },
        {
            "id": 60,
            "question": "Walk me through your complete end-to-end approach to preparing a raw dataset for a production classification model, from ingestion to feature matrix.",
            "difficulty": "Hard",
            "topic": "Data Preprocessing",
            "expected_keywords": [
                "EDA", "distribution", "outliers", "missing values", "encoding",
                "scaling", "train-test split", "leakage", "pipeline", "reproducible",
            ],
            "follow_up": "How do you ensure that your preprocessing pipeline does not cause data leakage between the training and test sets?",
        },
    ],

    # =========================================================================
    "Product Management": [
        # ── Easy ─────────────────────────────────────────────────────────────
        {
            "id": 61,
            "question": "What is a product roadmap? What should it contain, and how does it differ from a project plan or a backlog?",
            "difficulty": "Easy",
            "topic": "Product Roadmap",
            "expected_keywords": [
                "vision", "themes", "time horizon", "outcome", "OKR",
                "Now-Next-Later", "milestones", "not a Gantt chart", "stakeholders",
            ],
            "follow_up": "How do you communicate roadmap changes to stakeholders when priorities shift, without losing their trust?",
        },
        {
            "id": 62,
            "question": "What is an MVP (Minimum Viable Product)? How do you decide what makes it into the MVP and what gets cut?",
            "difficulty": "Easy",
            "topic": "MVP Definition",
            "expected_keywords": [
                "core value", "validate", "riskiest assumption", "user feedback",
                "iterate", "scope", "build-measure-learn", "launch", "must-have",
            ],
            "follow_up": "What is the difference between an MVP and a prototype, and when would you build one vs the other?",
        },
        {
            "id": 63,
            "question": "What is a north star metric? Give an example for a ride-sharing app and explain why a north star metric is better than tracking many KPIs.",
            "difficulty": "Easy",
            "topic": "North Star Metric",
            "expected_keywords": [
                "single metric", "user value", "growth", "lagging vs leading",
                "Uber rides completed", "focus", "alignment", "counter metric",
            ],
            "follow_up": "What is a counter metric, and why is it important to define one alongside your north star metric?",
        },
        {
            "id": 64,
            "question": "What happens during sprint planning in an agile team? Who participates, what are the key outputs, and what makes it effective?",
            "difficulty": "Easy",
            "topic": "Sprint Planning",
            "expected_keywords": [
                "sprint goal", "backlog refinement", "story points", "velocity",
                "capacity", "acceptance criteria", "team", "commitment", "scope",
            ],
            "follow_up": "How do you handle situations where the team's velocity estimate proves wrong mid-sprint?",
        },
        {
            "id": 65,
            "question": "How do you conduct a competitive analysis for a new product feature? What dimensions do you evaluate, and how do you use the findings?",
            "difficulty": "Easy",
            "topic": "Competitive Analysis",
            "expected_keywords": [
                "feature matrix", "differentiation", "positioning", "market gap",
                "strengths weaknesses", "pricing", "user reviews", "strategy",
            ],
            "follow_up": "How do you avoid the trap of building features just because a competitor has them?",
        },
        # ── Medium ────────────────────────────────────────────────────────────
        {
            "id": 66,
            "question": "How do you prioritize a product backlog? Describe the RICE framework and the MoSCoW method, and when you'd use each.",
            "difficulty": "Medium",
            "topic": "Prioritization Frameworks",
            "expected_keywords": [
                "RICE", "reach", "impact", "confidence", "effort",
                "MoSCoW", "must have", "should have", "could have", "won't have",
            ],
            "follow_up": "How do you prevent the loudest stakeholder from always winning the prioritization debate?",
        },
        {
            "id": 67,
            "question": "A product team is launching a checkout redesign. How do you define success metrics for this feature before it ships?",
            "difficulty": "Medium",
            "topic": "Success Metrics",
            "expected_keywords": [
                "conversion rate", "drop-off", "AOV", "primary metric", "guardrail",
                "leading indicator", "lagging indicator", "baseline", "HEART framework",
            ],
            "follow_up": "How do you decide how long to wait before declaring the feature a success or failure?",
        },
        {
            "id": 68,
            "question": "What user research methods do you use, and how do you decide which to apply at different stages of the product lifecycle?",
            "difficulty": "Medium",
            "topic": "User Research Methods",
            "expected_keywords": [
                "discovery", "validation", "user interview", "usability testing",
                "survey", "diary study", "jobs-to-be-done", "affinity mapping", "personas",
            ],
            "follow_up": "How do you synthesize qualitative research findings to make a persuasive case for a product direction?",
        },
        {
            "id": 69,
            "question": "Engineering wants 40% of the next quarter devoted to technical debt, but the business is pushing for new features. How do you navigate this?",
            "difficulty": "Medium",
            "topic": "Stakeholder Conflict",
            "expected_keywords": [
                "business impact", "risk", "velocity", "trade-off", "alignment",
                "data", "incremental", "negotiate", "trust", "engineering partnership",
            ],
            "follow_up": "How do you quantify the cost of technical debt in business terms so that non-technical stakeholders understand the urgency?",
        },
        {
            "id": 70,
            "question": "What does a go-to-market strategy include for a new B2B SaaS product? What are the key components from launch to adoption?",
            "difficulty": "Medium",
            "topic": "Go-to-Market Strategy",
            "expected_keywords": [
                "ICP", "positioning", "pricing", "channels", "sales motion",
                "launch", "pilot", "enablement", "feedback loop", "success criteria",
            ],
            "follow_up": "How would your GTM strategy differ if the product were B2C with a product-led growth motion instead?",
        },
        {
            "id": 71,
            "question": "How would you design an A/B test to evaluate a proposed redesign of the onboarding flow for a mobile app?",
            "difficulty": "Medium",
            "topic": "A/B Test Design",
            "expected_keywords": [
                "hypothesis", "control", "variant", "sample size", "duration",
                "primary metric", "guardrail", "segmentation", "statistical power", "significance",
            ],
            "follow_up": "The test has been running for two weeks and the result is barely significant (p = 0.049). Do you ship it? Why or why not?",
        },
        # ── Hard ──────────────────────────────────────────────────────────────
        {
            "id": 72,
            "question": "Our product's DAU has dropped 20% over the past month. Walk me through exactly how you would diagnose the root cause.",
            "difficulty": "Hard",
            "topic": "Declining DAU",
            "expected_keywords": [
                "segment", "cohort", "retention", "acquisition", "funnel",
                "external factor", "platform change", "competitor", "feature regression", "hypothesis",
            ],
            "follow_up": "You discover the drop is concentrated among users who installed the app more than 6 months ago. What does that tell you, and what do you do next?",
        },
        {
            "id": 73,
            "question": "How would you improve Gmail? Walk me through your problem definition, user research, prioritization, and top three feature recommendations.",
            "difficulty": "Hard",
            "topic": "Product Improvement",
            "expected_keywords": [
                "user segments", "pain points", "prioritization", "data",
                "north star", "power user", "smart features", "trade-off", "feasibility",
            ],
            "follow_up": "How would you validate that your proposed improvement actually solves the problem before committing to a full build?",
        },
        {
            "id": 74,
            "question": "How do you decide how much engineering time to invest in paying down technical debt vs building new features? Walk me through your framework.",
            "difficulty": "Hard",
            "topic": "Technical Debt Tradeoff",
            "expected_keywords": [
                "velocity", "risk", "developer experience", "quantify", "incident rate",
                "opportunity cost", "scheduled", "20% rule", "refactor", "ROI",
            ],
            "follow_up": "How would you build the business case for a quarter-long technical debt initiative to a skeptical CEO?",
        },
        {
            "id": 75,
            "question": "Walk me through how you would map the end-to-end customer journey for a food delivery app, and how you would use the map to identify the highest-impact improvement opportunity.",
            "difficulty": "Hard",
            "topic": "Customer Journey Mapping",
            "expected_keywords": [
                "touchpoints", "emotions", "pain points", "moments of truth",
                "awareness", "consideration", "retention", "NPS", "drop-off", "opportunity scoring",
            ],
            "follow_up": "How do you keep a customer journey map current as the product and user behaviour evolve over time?",
        },
    ],
}


# ── Helper functions ───────────────────────────────────────────────────────────

def get_questions(
    domain: str,
    count: int,
    difficulty: Optional[str] = None,
) -> list[dict]:
    """
    Return a shuffled list of `count` questions from `domain`.
    If `difficulty` is specified, filter to only that difficulty level.
    Falls back to the full pool if the filtered pool is too small.
    Each returned dict includes question_number (1-indexed) added for display.
    """
    pool = QUESTIONS.get(domain, [])
    if difficulty:
        filtered = [q for q in pool if q["difficulty"] == difficulty]
        # If filtered pool has enough, use it; otherwise fall back to full pool
        pool = filtered if len(filtered) >= count else pool

    selected = random.sample(pool, min(count, len(pool)))
    return [
        {**q, "question_number": i + 1}
        for i, q in enumerate(selected)
    ]


def get_random_followup(domain: str) -> str:
    """Return a random follow-up question string from the given domain."""
    pool = QUESTIONS.get(domain, [])
    if not pool:
        return "Can you expand on that?"
    return random.choice(pool)["follow_up"]


def get_all_domains() -> list[str]:
    """Return the list of all available domain names."""
    return list(QUESTIONS.keys())


def get_topic_list(domain: str) -> list[str]:
    """Return a sorted list of unique topic tags for the given domain."""
    pool = QUESTIONS.get(domain, [])
    return sorted({q["topic"] for q in pool})
