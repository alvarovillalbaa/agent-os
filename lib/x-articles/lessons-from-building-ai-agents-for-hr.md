# Lessons from Building AI Agents for Human Resources

I've spent 3+ years thinking about this AI for HR teams. There are too many counterintuitive lessons we learned building AI agents for the most hated department in every organization.

## HR Is the Hardest Domain for AI

This is no surprise.

Finance is deterministic. Code is testable and reproducible. You can validate outputs against expected results. If a function returns the wrong number, you know.

**HR is none of those things.**

Firing someone. Putting someone on a PIP. Evaluating whether a candidate is the right fit. These are high-stakes, non-deterministic, non-testable, non-reproducible decisions. There's no unit test for "was this person the right one to get fired?"

That's what makes building AI for HR fundamentally different from building it for code generation or financial analysis. These decisions affect people's lives in ways that are hard to quantify and impossible to roll back.

[IMAGE: Simple comparison diagram — Finance/Code (deterministic, testable, reproducible) vs HR (non-deterministic, non-testable, non-reproducible)]


## Too Much Data, Not Enough Information

Here's the paradox we kept running into.

HR teams sit on mountains of data. Employment contracts can be 30+ pages long. But the actually useful information, like reference to applicable law, salary, job role, is just one paragraph.

**The information-to-data ratio in HR is painfully low.**

And the data that matters most is continuously generated, manually collected, and distributed across a dozen systems. Nobody owns it cleanly. Nobody has a single view of it. Take candidate applications, cross-employee feedback, satisfaction surveys as examples.

This is the core infrastructure problem of HR tech, and most AI products are just a chatbot on top of it instead of solving it.


## Multi-Player AI Is Not Optional

HR teams have deep hierarchies. A single decision — say, a promotion or a hiring choice — might involve the direct manager, the HRBP, the department head, the compensation team, and sometimes legal.

**Building AI for HR means building multi-player AI.** Human-in-the-loop is not a nice-to-have. It's the entire point. And it's not just one human — it's a committee.

This changes everything about how you design the system. You need collaborative workflows where AI surfaces recommendations and multiple stakeholders confirm, reject, or modify them. Not a single user pressing a button.

Most AI products are designed for a single user. HR doesn't work that way.

[IMAGE: Diagram showing a single AI recommendation flowing to multiple stakeholders (HRBP, Manager, Department Head, Comp Team) for collaborative approval]


## Most AI-for-HR Use Cases Are Wrong

The market is getting wrong most use cases.

**Resume parsing.** This has been done for 15 years. It's low value-add. It was commoditized before LLMs existed.

**Payroll automation.** Payroll is deterministic. It was already automated. You don't need AI to send the right amount of money to the right person. What you might need AI for is payroll budgeting, analysis, forecasting, and calibration — but that's a completely different problem.

**Pre-onboarding data entry.** Some companies are building an AI UX to help employees enter their bank account and ID documentation. But employees have to input this data manually either way. An AI layer on top of a form is just more confusing and adds zero value.

Now compare all of that to this: decide who's best for a role among thousands of candidates who applied and who didn't, automate the workflow up to scheduling the first interview with personalized outreach messaging, and process post-interview transcripts automatically.

One is incremental improvement on solved problems. The other is a 10x change in how recruiting operates.

The difference? The wrong use cases automate a task. The right ones automate an entire workflow.


## The Use Cases That Actually Win

After building in this space, two use cases stand out above everything else.

### 1. Reporting

Right now, HR reporting works like this: build a form to collect data, export it to a spreadsheet, build a slides deck, present it to stakeholders. All manual. Takes weeks.

What it should look like: data collected continuously throughout the year, dashboards built automatically, slides decks generated in seconds. **The entire pipeline from data collection to executive presentation is ripe for automation.**

This isn't flashy. Nobody puts "automated reporting" in a pitch deck headline. But it saves HR teams hundreds of hours per year — and it makes the data actually useful instead of stale by the time anyone sees it.

### 2. Employee Support

Think of it as Customer Support AI — but for the internal client: the employee.

Customer Support is one of the winning industries in AI right now ( @sierra ), along with Coding and Legal.

Employees ask HR the same questions constantly. Benefits eligibility. PTO policies. Expense rules. Parental leave. This is a textbook case for AI agents: high volume, repetitive, well-documented answers, and immediate value for both the employee (faster answers) and HR (less time on tickets).

**These two aren't flashy. They're not "AI avatars conducting interviews." But they solve real, expensive, recurring pain.**

[IMAGE: Before/After — Before: Forms → XLSX → Slides (weeks). After: Continuous data collection via Slack → Auto-dashboards → Instant slides (seconds)]

---

## Data Ownership Will Make or Break You

This is the lesson most builders learn too late.

HR tech has hundreds of competitors. You could build 1,000+ integrations. But then you own no data.

A few years back, **LinkedIn stopped providing API access to ATS platforms** and the entire recruiting market has been drowning ever since. The same happened from LinkedIn to Sales Tech over the past two years.

If you're building in HR tech, your data strategy is your survival strategy.

Our mindset:

- **Capture 10x more data** than other platforms do.
- **Own workflows end-to-end** to own the data those workflows produce.
- **Standard generalized integrations only** — Slack, Google Drive, etc. — maximum one custom integration per customer, and only if it benefits at least two customers.

**If your value depends on another platform's API, you're one policy change away from irrelevance.**

This applies to HR teams too. When evaluating vendors, ask yourself: who actually owns the data your team generates? If the answer is "the vendor" — you have a problem.


## What Everyone Already Knows About AI Agentic Systems Design

A few principles that kept proving themselves:

**The AI system must continuously learn.** HR data changes constantly — new hires, role changes, performance shifts. An AI agent that only knows what it was trained on is useless within weeks.

**Memory is really important.** Context from past conversations, previous decisions, historical patterns — this is what makes an AI system feel intelligent instead of starting from scratch every interaction.

**The orchestration layer is where value accrues.** Individual AI capabilities — summarization, classification, generation — are commodities. The orchestration of multiple agents working together on complex, multi-step HR workflows? That's where the defensible product lives.

**Scaffolding of the system of agents matters a lot.** How you structure which agent handles what, how they hand off to each other, how they escalate to humans — this architecture *is* your product. Get it wrong and you have a collection of demos. Get it right and you have a system that actually works in production.


## Key Takeaways

**1. HR is non-deterministic.** You can't build AI for HR the same way you build it for code or finance. Human-in-the-loop is the design principle, not a fallback.

**2. Most AI-for-HR use cases are wrong.** Resume parsing and payroll automation are solved problems. Reporting and employee support are where the real value is.

**3. The information-to-data ratio is terrible.** 30-page contracts with one useful paragraph. The real challenge isn't having data — it's extracting information from the noise.

**4. Data ownership is existential.** If you don't own the data, you don't own the business. The LinkedIn API shutdown proved this for the entire industry.

**5. Multi-player AI is the default.** HR decisions involve committees, not individuals. Design for that from day one.

**6. The orchestration layer is the product.** Individual AI capabilities are commodities. The system design is the moat.


HR is the most hated department in most organizations. I think that's partly because it's also the most misunderstood — and the most underserved by technology.
