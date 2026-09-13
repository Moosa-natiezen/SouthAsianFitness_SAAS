# Reddit Launch Post — r/SideProject

> **Copy-paste ready.** Post the title below as the Reddit title; everything under the divider is the post body.
> Best posted Tue–Thu, 8–11am EST. Reply to every comment in the first 2 hours — Reddit's algorithm rewards early engagement.

---

## Title

**I got tired of MyFitnessPal telling me my mom's Daal was "150g mixed vegetables" — so I spent 6 months building a fitness app that actually understands Desi food**

## Body

Hey everyone 👋

Solo dev here. I want to show you something I've been building in public for the past 6 months, and I'm specifically asking for **harsh feedback** — tear it apart if needed.

### The problem (you probably live it)

If you're South Asian and you've ever tried to track your food, you know the pain:

- MyFitnessPal has **"1 cup daal"** logged by some random user as 400 calories. Another entry says 120. Nobody knows which is right.
- There is no decent entry for **Nihari, Haleem, Karahi, or Sarson ka Saag** — and if there is one, the macros are pure fiction.
- So we all do the same thing: give up, eyeball it, and wonder why the scale doesn't move.

I got especially tired of the classic **"grilled chicken breast, broccoli, and brown rice"** advice every generic fitness app gives. That's not a meal plan my mom would recognize, and frankly, it's not a diet anyone can sustain for life. Roti, Daal, and Sabzi are *not* the enemy — untracked portions are.

### What I built

**South Asian Fitness** — a fitness app where the entire food database and AI engine is built around Desi cuisine from day one:

- 🍛 **A verified South Asian food database** — Biryani, Daal, Roti, Paratha, Chana, Paneer dishes, Karahi — with real portion sizes (per roti, per katori, per serving), not vague "100g" guesses
- 🤖 **An AI meal-plan engine with a strict Desi mandate** — it's explicitly forbidden from generating "plain grilled chicken with broccoli" fitness meals. It works with what your kitchen actually has: Atta, Daal, yogurt, Desi spices, and yes, it still hits your macros
- 🎯 **Macro calculation tuned for our food** — because 2 rotis + a bowl of salan hits differently than a protein shake
- 💪 **Workout plans too**, if you want the full stack

### How it's built (for the nerds)

- **Next.js** frontend + **FastAPI** backend
- Protected by **custom rate-limiting and abuse protection** on the AI endpoints (they cost real tokens, and Reddit will absolutely stress-test that for me 😅)
- Streaming AI generation, deterministic macro engine underneath, and a free tier so you can try it properly

### What I need from you

Be brutal. Specifically:

1. **Sign up and break it** → [southasianfitness.com](https://southasianfitness.com)
2. Generate a meal plan for food you actually eat. Is it culturally accurate — or a generic "curry" stereotype?
3. Check the macros for a food you know well. Where did I get it wrong?
4. Tell me what's missing. What would make you actually use this daily?

I'm looking for **beta testers who eat Desi food every day** — if that's you, your feedback is worth more than any paid research panel.

Free tier is generous on purpose. No credit card, no paywall games.

---

*Happy to answer anything about the stack, the food data curation (the hard part, by far), or the AI pipeline. Roast away.* 🔥
