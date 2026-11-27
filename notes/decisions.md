# Platform: decisions

## 1. Goal and audience
Questions:
- Who is it for first: students, teachers, or both? Which grades? - Students, who are searching for database of problems and their solutions. Teachers also can use with the feature of pdf compiler
- What should a visitor be able to do in the first 30 seconds? Choose the topic they are about to learn and see every subtopic, probably open first tasks in chosen subtopic
- What does "success" look like in 6 months (number of problems, visitors, something else)? Number of problems definitely more than 5000, I think around 10000, because it will contain all problems from olympiads that are available online, also some excesrices and suggested journeys of learing, like theoretical material and then set of corresponding problems.
users: I would say up to a few thousand per month.

## 2. Hosting and infrastructure
- Database on cloudfare R2
- Cloudflare for hosting and the domain.
- Content is built in GitHub Actions (TeX Live + pandoc), then deployed. (or just in cloudfare???)

Questions:
- Cloudflare Pages or GitHub Pages for the site itself? lets use only cloudfare
- Where do the ~100 large PDFs live (in the repo, Cloudflare R2, other)? R2
- Maximum monthly cost you accept? for now it is zero, if there will be visitors - around 30 bucks

## 3. Content
Known so far:
- Problems are written in LaTeX, one `.tex` file per problem, with a metadata header.
- Same `id` links the RU version, EN version and solution file.

Questions:
- Which problem fields must exist for every problem (topic, difficulty, source, year, grade, others)? topic, subtopic, diffictuly (1, 2, 3), source, year, grade
- Are solutions in scope? Not now, solutions should be available when loading the task. But for now I wont load solutions, only problem statements
- Do old problems that exist only as photos or PDFs go on the site? I will convert them into latex or another convenient form before uploading 
- Who is allowed to add content: only you, or others later? only me
- Do you need theory notes (conspects) on the site? In the MVP? yes, not in mvp. Keep the theory notes tab, but place there placeholder saying that it is still in developement

## 4. Languages
Known so far: RU and EN.

Questions:
- Is every problem available in both languages, or only some? in mvp, tasks from russian olympiads are in ru, from international olympiads - in english. Later I will add both eng version for each russian olympiad problem
- Which language is the default? Does the interface switch by a button or by URL (`/ru/`, `/en/`)? default is russian, switched by a button ru/en on the website
- Who translates, and how are untranslated problems shown? You will translate them, marking for review after translation. Before we have translation each problem is in its origianl language


## 5. MVP scope
Known so far: list pages and filters first, PDF export later.

Questions:
- What must the MVP have to be worth publishing? (home star map, problem list, filters, ...) - home star map, topics and subtopics division, all filters 
- What is explicitly not in the MVP? Solutions, two languages for russian problems, theory notes, games attached, recommended study order/courses
- What comes right after the MVP, in order? games attached, theory notes, study order, two languages, solutions 
- Target date for the MVP? middle of december 2026


## 6. Structure and design
Known so far:
- Home page is a star map of topics. Click a star, see the subtopic list, then the problem list.
- Style: Ink sketchbook (black-ink doodles on white), spacious, minimal, hand-drawn dividers, readable body font, no all-caps UI text, no all uppercase text for titles and different notes.

Questions:
- List every page the site needs (home, topic page, problem page, about, games, ...). Home page (that will show subtopics list after clicking on a topic and also have search engine for searching through all question bank), problems page (where it will be possible to navigate through the subtopics and filters), theory page, games' pages, courses' page
- Does a problem have its own page or only a row in a list? For now only row in a list, later each problem has its own page with solution
- Mobile: must it work well on phones in the MVP? we dont care about mobile use rn, after mvp 
- Any accessibility needs (contrast, font size, keyboard use)? no

## 7. Games
Questions:
- Which games (ConstellationGame, ConstellationFinder), and are they finished? they are kinda finished, I will do them after nvp is ready
- Are they static files you can host on the same site, or do they need something else? no, they are not static
- How are they linked (home page bottom, own page)? home page buttom opens the maindomain.gamename (or gamename.maindomain ?) with its own interface and design

## 8. Name and domain
Known so far: leading option is Atria + astro (atriaastro). Domain is separate from the brand name.

Questions:
- Final name, or still open? What would decide it? still unsure, lets put stellar task for now, then I will change it
- Which domain, and is it registered on Cloudflare? tsvetkovaspace.com , I will change it later
- Is there an Instagram account to match the name? Not yet

## 9. Your workflow
Questions:
- How will you add a new problem? (write a `.tex` file, run a check, commit, push?) Ideally I would like separate interface for it, but in nvp only through ide is fine
- Which editor do you write LaTeX in? overleaf 
- How often will you add content (weekly, in bursts after camps)? I think I will create a routine for you, and you will add small sets of tasks daily after the structure is ready
- What would make editing annoying enough that you'd stop? idk for now

## 10. Constraints
Questions:
- How many hours a week can you spend on this? Up to 10 hours of my time, but claude can work while I am having a rest
- Claude usage budget: which plan, and how do you want to use it (a few big sessions or many small ones)? pro one, many small ones
- Anything you refuse to do (for example run a backend, pay for hosting, use a framework you don't know)? I was suggested to use Astro for front, Pagefind, KaTeX 

## 11. Problem lists (2026-11-27)
- Numbered pages of 20 problems per subtopic (`/problems/<topic>/<subtopic>/<n>/`). The filters cover the whole
  subtopic: the browser collects matching rows from the other static pages.
