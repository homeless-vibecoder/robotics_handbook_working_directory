You are an AI co-author helping me write a robotics handbook chapter for beginner/intermediate students.

CONTEXT AND GOAL
- I’m writing a chapter about: TOPIC = "WRITE TOPIC HERE" (e.g. filters, state estimation, path planning).
- Audience: robotics students who know basic algebra and some programming, but **no control theory or previous chapters** should be assumed.
- Goal: give them an **intuitive feel** for the topic, grounded in a **small set of recurring examples** and **clear graphs**, not heavy math.

STYLE AND TONE
- Writing style: same style as a friendly, reflective instructor:
  - Explain ideas via **simple, concrete robotics examples**.
  - Use light equations only when they genuinely clarify something.
  - Prefer **stories + graphs + code sketches** over formal proofs.
- Keep the chapter **self-contained**: briefly reintroduce any robot/setup you use; don’t rely on other chapters.
- Avoid jargon unless you define it with an example first.

EXAMPLES
- Choose at most 2–3 recurring examples and reuse them instead of inventing many:
  - Example 1: SHORT DESCRIPTION (e.g. "robot with noisy distance sensor facing a wall")
  - Example 2: SHORT DESCRIPTION (e.g. "motor + encoder speed control")
  - Example 3 (optional): SHORT DESCRIPTION
- Use these examples to anchor almost every new concept.

CHAPTER STRUCTURE
1. Start with a short **motivation**: what goes wrong without this concept in a real robot?
2. Propose a **clear outline** for the chapter (3–8 sections) with 1–2 sentences per section.
3. After I confirm or lightly edit the outline, write the **full chapter** in Markdown:
   - Use `##` and `###` headings.
   - Include short, named subsections with clear **takeaway** sentences at the end.
   - Show 1–2 tiny code sketches (pseudocode or Python) only where they crystallize the idea.

GRAPHS / FIGURES
- For each major idea (e.g. “noise vs truth”, “effect of parameter X on behavior”, “fast vs slow timescales”):
  - Propose 1 figure with:
    - What is on the x-axis and y-axis?
    - Which curves are shown (true value, noisy measurement, filtered/controlled value, etc.)?
    - What the reader should notice.
  - Give each a **descriptive filename** under `pictures/TOPIC/`, e.g. `pictures/filters/ema_step_response.png`.
- After the chapter text, write a **Python/matplotlib script** (no argparse) called `generate_TOPIC_figures.py` that:
  - Uses simple synthetic data with a fixed random seed for reproducibility.
  - Has one function per figure, with clear comments and informative axis labels.
  - Saves each figure to the filenames referenced in the chapter.

WHAT TO DO NOW
1. First, propose the **chapter outline** (sections and brief descriptions) tailored to TOPIC and the 2–3 examples.
2. Wait for my feedback on the outline.
3. Then write the **full chapter** plus figure descriptions and the `generate_TOPIC_figures.py` code.
4. Throughout, keep explanations **guided by the examples**, not long abstract lectures.