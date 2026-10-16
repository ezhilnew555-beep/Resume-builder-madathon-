import type {
  ReadinessScore,
  ResumeSection,
  ReviewFinding,
  JobMatchAnalysis,
  ProfileConnection,
  LearningTask,
  CareerReport,
  StudentProfile,
} from '../types';

export const mockReadinessScore: ReadinessScore = {
  overall: 78,
  atsScore: 84,
  skillAlignment: 72,
  experienceImpact: 76,
  presentation: 88,
  tier: 'Nearly Ready',
};

export const mockResumeSections: ResumeSection[] = [
  {
    id: 'contact',
    title: 'Contact Information',
    content: 'Alex Rivera | Seattle, WA | alex.rivera@example.com | (555) 019-2834 | linkedin.com/in/alex-rivera-dev | github.com/alexrivera-tech',
    wordCount: 18,
    completeness: 100,
  },
  {
    id: 'summary',
    title: 'Professional Summary',
    content: 'Full-stack software engineer with 2+ years of hands-on experience developing web applications using React, TypeScript, Python (FastAPI), and PostgreSQL. Proven track record of optimizing database query latency by 35% and building responsive, accessible client interfaces.',
    wordCount: 38,
    completeness: 90,
  },
  {
    id: 'experience',
    title: 'Work Experience',
    content: `Associate Software Engineer | CloudScale Systems | Jan 2024 - Present
• Designed and developed 14+ RESTful API endpoints using FastAPI and Pydantic, supporting 120k daily active users.
• Refactored React front-end state management using TanStack Query and Zustand, decreasing initial bundle load time by 28%.
• Implemented automated CI/CD pipeline using GitHub Actions, cutting release deployment turnaround from 4 hours to 18 minutes.
• Participated in weekly code reviews and authored comprehensive API documentation with OpenAPI 3.0 specs.

Software Developer Intern | Nexus Byte Innovations | Jun 2023 - Dec 2023
• Built reusable React component library in TypeScript adhering to WCAG 2.1 AA accessibility guidelines.
• Optimized PostgreSQL indexing and schema queries for a high-volume analytics dashboard, reducing 95th percentile load latency from 1.8s to 420ms.
• Collaborated in a 5-person agile team with daily stand-ups and two-week sprint retrospectives.`,
    wordCount: 142,
    completeness: 85,
  },
  {
    id: 'skills',
    title: 'Technical Skills',
    content: 'Languages: Python, TypeScript, JavaScript, SQL, HTML5, CSS3\nFrameworks: FastAPI, React, Node.js, Express, Tailwind CSS, Next.js\nDatabases & Cloud: PostgreSQL, Supabase, Redis, AWS (S3, Lambda), Docker\nDeveloper Tools: Git, GitHub Actions, Linux/Bash, Postman, Jest, Vitest',
    wordCount: 35,
    completeness: 95,
  },
  {
    id: 'education',
    title: 'Education',
    content: 'B.S. in Computer Science | University of Washington | Graduated May 2024\nCumulative GPA: 3.82 / 4.0 | Dean\'s Honor List (6 Quarters)\nRelevant Coursework: Distributed Systems, Database Management Systems, Data Structures & Algorithms, Cloud Computing.',
    wordCount: 34,
    completeness: 90,
  },
  {
    id: 'projects',
    title: 'Technical Projects',
    content: `PulseBoard — Real-time Distributed Metrics Visualizer (TypeScript, React, WebSockets, Python, Redis)
• Engineered real-time dashboard displaying system telemetry streamed over WebSockets with <50ms latency.
• Integrated Redis pub/sub to handle concurrent broadcast bursts across 5,000 simulated nodes.

DocuSense — Semantic Document Search Engine (Python, FastAPI, Vector Search, Docker)
• Created semantic search service using embedding cosine similarity over 50,000 PDF research publications.
• Packaged backend services into Docker containers deployed with automated healthcheck probes.`,
    wordCount: 78,
    completeness: 88,
  },
];

export const mockReviewFindings: ReviewFinding[] = [
  {
    id: 'find-1',
    type: 'error',
    category: 'Contact Consistency',
    title: 'Unclickable and non-standard LinkedIn hyperlink representation',
    location: 'Contact Information > Header',
    explanation: 'ATS parsers frequently fail to resolve partial LinkedIn URLs without explicit scheme headers (e.g., https://).',
    proposedCorrection: 'Use full standard canonical URL: "https://linkedin.com/in/alex-rivera-dev" or clean hypertext label.',
    status: 'pending',
    originalSnippet: 'linkedin.com/in/alex-rivera-dev',
  },
  {
    id: 'find-2',
    type: 'improvement',
    category: 'Impact Metrics',
    title: 'Internship bullet #3 lacks measurable business impact',
    location: 'Work Experience > Nexus Byte Innovations > Bullet 3',
    explanation: '"Collaborated in a 5-person agile team" describes attendance rather than demonstrable engineering outcomes.',
    proposedCorrection: 'Rewrite: "Delivered 18 sprint features on schedule within a 5-person agile team, maintaining zero production regressions across the 6-month internship period."',
    status: 'pending',
    originalSnippet: 'Collaborated in a 5-person agile team with daily stand-ups and two-week sprint retrospectives.',
  },
  {
    id: 'find-3',
    type: 'missing',
    category: 'Domain Certifications',
    title: 'Missing cloud certification or verified accreditation section',
    location: 'Resume Structure > After Education',
    explanation: 'For mid-level cloud and backend positions, having AWS Certified Cloud Practitioner or Solutions Architect elevates ATS ranking by up to 22%.',
    proposedCorrection: 'Add a "Certifications" section listing completed or in-progress credentials (e.g. AWS Certified Cloud Practitioner - Expected Nov 2026).',
    status: 'pending',
    originalSnippet: '[No Certifications section found]',
  },
  {
    id: 'find-4',
    type: 'keyword',
    category: 'ATS Keywords',
    title: 'Missing high-demand distributed systems keywords',
    location: 'Technical Skills > Databases & Cloud',
    explanation: 'Target senior backend and fullstack postings commonly filter for "Kubernetes", "Microservices", and "gRPC".',
    proposedCorrection: 'Add hands-on or academic experience with container orchestration: "Kubernetes, Microservices Architecture, gRPC (familiar)".',
    status: 'pending',
    originalSnippet: 'Databases & Cloud: PostgreSQL, Supabase, Redis, AWS (S3, Lambda), Docker',
  },
  {
    id: 'find-5',
    type: 'improvement',
    category: 'Action Verbs',
    title: 'Repeated action verb in project section',
    location: 'Technical Projects > DocuSense > Bullet 1',
    explanation: 'Passive or simple verbs like "Created" reduce recruiter engagement compared to impactful engineering action verbs.',
    proposedCorrection: 'Replace "Created semantic search service" with "Architected high-throughput semantic search pipeline".',
    status: 'pending',
    originalSnippet: 'Created semantic search service using embedding cosine similarity...',
  },
];

export const mockJobMatchAnalysis: JobMatchAnalysis = {
  id: 'match-894',
  targetRole: 'Full Stack Software Engineer (React / Python)',
  targetCompany: 'FinTech Velocity Labs',
  overallMatchScore: 82,
  hardSkillMatchScore: 86,
  experienceMatchScore: 78,
  verifiedEvidenceSummary: '7 out of 9 core job requirements are verified with direct citations from the candidate resume. 2 key gaps were detected in container orchestration and message queuing at scale.',
  matchedRequirements: [
    {
      name: 'React & TypeScript Development',
      category: 'framework',
      level: 'advanced',
      evidenceQuote: 'Refactored React front-end state management using TanStack Query and Zustand... Built reusable React component library in TypeScript adhering to WCAG 2.1 AA.',
      location: 'Experience (CloudScale Systems & Nexus Byte)',
      confidence: 96,
    },
    {
      name: 'Python & RESTful Backend (FastAPI)',
      category: 'core',
      level: 'advanced',
      evidenceQuote: 'Designed and developed 14+ RESTful API endpoints using FastAPI and Pydantic, supporting 120k daily active users.',
      location: 'Experience > CloudScale Systems',
      confidence: 98,
    },
    {
      name: 'Relational Database Optimization (PostgreSQL)',
      category: 'core',
      level: 'advanced',
      evidenceQuote: 'Optimized PostgreSQL indexing and schema queries for a high-volume analytics dashboard, reducing 95th percentile load latency from 1.8s to 420ms.',
      location: 'Experience > Nexus Byte Innovations',
      confidence: 94,
    },
    {
      name: 'CI/CD & Automated Pipeline Deployment',
      category: 'tools',
      level: 'intermediate',
      evidenceQuote: 'Implemented automated CI/CD pipeline using GitHub Actions, cutting release deployment turnaround from 4 hours to 18 minutes.',
      location: 'Experience > CloudScale Systems',
      confidence: 90,
    },
    {
      name: 'Caching & In-Memory Data Stores (Redis)',
      category: 'tools',
      level: 'intermediate',
      evidenceQuote: 'Integrated Redis pub/sub to handle concurrent broadcast bursts across 5,000 simulated nodes.',
      location: 'Projects > PulseBoard',
      confidence: 85,
    },
  ],
  skillGaps: [
    {
      name: 'Kubernetes & Container Orchestration',
      importance: 'Required',
      frequencyInJD: 4,
      learningDifficulty: 'Medium',
      recommendedResource: 'CKAD Certification Crash Course & Minikube hands-on deployment guide',
    },
    {
      name: 'Message Queues (Kafka or RabbitMQ)',
      importance: 'Required',
      frequencyInJD: 3,
      learningDifficulty: 'Medium',
      recommendedResource: 'Architecting Event-Driven Systems with Apache Kafka (Hands-on Lab)',
    },
    {
      name: 'End-to-End Testing (Cypress / Playwright)',
      importance: 'Preferred',
      frequencyInJD: 2,
      learningDifficulty: 'Low',
      recommendedResource: 'Automated Browser Testing with Playwright in TypeScript',
    },
  ],
  recommendations: [
    'Deploy the PulseBoard project into a local Minikube cluster and document Helm charts to prove Kubernetes capability.',
    'Replace one Redis pub/sub reference with an event-driven Kafka broker worker to directly address the JD distributed messaging requirement.',
    'Add automated Playwright smoke tests to your GitHub Actions pipeline and document them explicitly under Experience.',
  ],
};

export const mockProfileConnections: ProfileConnection[] = [
  {
    id: 'github',
    name: 'GitHub',
    iconName: 'Github',
    description: 'Verify public repositories, commit cadence, language distribution, and pull requests.',
    status: 'connected',
    usernameOrUrl: 'github.com/alexrivera-tech',
    lastSynced: '2 hours ago',
    metricsPreview: [
      { label: 'Public Repos', value: '24' },
      { label: 'Contributions (2026)', value: '648' },
      { label: 'Top Languages', value: 'TS, Python, Go' },
    ],
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    iconName: 'Linkedin',
    description: 'Sync professional headline, validated recommendations, and career timeline.',
    status: 'connected',
    usernameOrUrl: 'linkedin.com/in/alex-rivera-dev',
    lastSynced: '1 day ago',
    metricsPreview: [
      { label: 'Connections', value: '450+' },
      { label: 'Profile Completeness', value: '98%' },
      { label: 'Skills Endorsed', value: '14' },
    ],
  },
  {
    id: 'leetcode',
    name: 'LeetCode',
    iconName: 'Code2',
    description: 'Track algorithm proficiency, contest ratings, and problem-solving badges.',
    status: 'connected',
    usernameOrUrl: 'leetcode.com/u/arivera_codes',
    lastSynced: '3 days ago',
    metricsPreview: [
      { label: 'Solved Problems', value: '312' },
      { label: 'Contest Rating', value: '1,845' },
      { label: 'Top Badge', value: 'Knight' },
    ],
  },
  {
    id: 'hackerrank',
    name: 'HackerRank',
    iconName: 'Award',
    description: 'Validate verified domain skill certificates (Python, SQL, Problem Solving).',
    status: 'not_connected',
    usernameOrUrl: '',
    metricsPreview: [],
  },
  {
    id: 'portfolio',
    name: 'Personal Portfolio',
    iconName: 'Globe',
    description: 'Verify live application demos, SSL security, responsive UI, and custom domain setup.',
    status: 'connected',
    usernameOrUrl: 'https://alexrivera.dev',
    lastSynced: '5 days ago',
    metricsPreview: [
      { label: 'Lighthouse Score', value: '98/100' },
      { label: 'Live Demos', value: '4 Apps' },
    ],
  },
  {
    id: 'kaggle',
    name: 'Kaggle',
    iconName: 'BarChart2',
    description: 'Showcase data science competitions, reproducible Jupyter notebooks, and datasets.',
    status: 'not_connected',
    usernameOrUrl: '',
    metricsPreview: [],
  },
];

export const mockLearningTasks: LearningTask[] = [
  {
    id: 'task-1',
    title: 'Containerize FastAPI & React with Multi-Stage Docker & Compose',
    skill: 'Docker & Microservices',
    category: 'Project',
    estimatedHours: 4,
    difficulty: 'Intermediate',
    status: 'completed',
    linkUrl: 'https://docs.docker.com/get-started/',
  },
  {
    id: 'task-2',
    title: 'Deploy Distributed Service to Minikube with Ingress & Secrets',
    skill: 'Kubernetes',
    category: 'Project',
    estimatedHours: 8,
    difficulty: 'Advanced',
    status: 'in_progress',
    linkUrl: 'https://kubernetes.io/docs/tutorials/hello-minikube/',
  },
  {
    id: 'task-3',
    title: 'Implement Event Streaming Producer-Consumer with Apache Kafka in Python',
    skill: 'Distributed Messaging',
    category: 'Practice',
    estimatedHours: 6,
    difficulty: 'Advanced',
    status: 'not_started',
    linkUrl: 'https://kafka.apache.org/documentation/',
  },
  {
    id: 'task-4',
    title: 'Automate Browser Regression Suite using Playwright & TypeScript',
    skill: 'End-to-End Testing',
    category: 'Practice',
    estimatedHours: 5,
    difficulty: 'Intermediate',
    status: 'not_started',
    linkUrl: 'https://playwright.dev/docs/intro',
  },
  {
    id: 'task-5',
    title: 'AWS Certified Cloud Practitioner Foundational Prep',
    skill: 'Cloud Architecture',
    category: 'Certification',
    estimatedHours: 14,
    difficulty: 'Beginner',
    status: 'in_progress',
    linkUrl: 'https://aws.amazon.com/certification/certified-cloud-practitioner/',
  },
];

export const mockReports: CareerReport[] = [
  {
    id: 'rep-101',
    date: 'Oct 14, 2026',
    resumeName: 'Alex_Rivera_Software_Eng_v2.pdf',
    targetRole: 'Full Stack Software Engineer',
    overallScore: 78,
    atsScore: 84,
    matchScore: 82,
    status: 'completed',
  },
  {
    id: 'rep-102',
    date: 'Oct 02, 2026',
    resumeName: 'Alex_Rivera_Software_Eng_v1.docx',
    targetRole: 'Junior Backend Developer',
    overallScore: 69,
    atsScore: 72,
    matchScore: 74,
    status: 'completed',
  },
  {
    id: 'rep-103',
    date: 'Sep 21, 2026',
    resumeName: 'Alex_Rivera_General_Resume.pdf',
    targetRole: 'Frontend React Developer',
    overallScore: 63,
    atsScore: 68,
    matchScore: 65,
    status: 'completed',
  },
];

export const mockStudentProfile: StudentProfile = {
  fullName: 'Alex Rivera',
  email: 'alex.rivera@example.com',
  phone: '+1 (555) 019-2834',
  location: 'Seattle, WA (Open to Relocation)',
  university: 'University of Washington',
  degree: 'B.S. in Computer Science',
  graduationYear: '2024',
  targetRole: 'Full Stack Software Engineer / Backend Engineer',
  preferredIndustries: ['FinTech', 'Cloud Infrastructure', 'Enterprise SaaS', 'HealthTech'],
  workPreference: 'Hybrid',
  scoringStrictness: 'Standard ATS',
  emailAlerts: true,
};

export const sampleJobDescriptions = [
  {
    company: 'FinTech Velocity Labs',
    title: 'Full Stack Software Engineer (React / Python)',
    text: `About the Role:
FinTech Velocity Labs is seeking a Full Stack Software Engineer to build scalable, low-latency financial settlement platforms. You will work across modern React/TypeScript frontends and high-performance Python/FastAPI microservices.

Core Requirements:
• 2+ years of professional engineering experience with Python and FastAPI or modern async frameworks.
• Strong command of React 18+, TypeScript, and component state architectures.
• Solid background in relational databases (PostgreSQL) including query planning, indexing, and connection pooling.
• Experience designing, building, and securing RESTful APIs using OpenAPI standards.
• Familiarity with containerized workflows using Docker and Kubernetes.
• Familiarity with distributed caching (Redis) and event streaming architectures (Kafka or RabbitMQ).
• Proven track record of testing pipelines (unit, integration, and E2E with Playwright or Cypress).
• Excellent communication skills and enthusiasm for peer code reviews.`,
  },
  {
    company: 'Starlight Cloud Security',
    title: 'Cloud Backend Engineer (Python / Distributed Systems)',
    text: `About the Role:
Join our cloud threat detection team building automated telemetry analysis pipelines processing millions of events per second.

Key Responsibilities:
• Build resilient backend ingestion services using Python, FastAPI, and Go.
• Manage PostgreSQL and ClickHouse clusters with high query throughput.
• Orchestrate services in Kubernetes on AWS with Terraform IaC.
• Implement automated CI/CD testing with PyTest and GitHub Actions.`,
  },
];
