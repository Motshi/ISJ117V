# Smart CV & Career Path Recommendation Platform — Frontend Prototype

This is a real, runnable React project (built with Vite) containing the
clickable prototype you already reviewed in chat: login, dashboard, CV
upload, job matches, applications, and profile — all with placeholder data,
no backend connected yet.

## Tech used (if anyone asks)
- **React** — JavaScript library for building the UI
- **Vite** — dev server / build tool that runs React projects
- Plain CSS (custom design tokens defined in the component) — no styling
  framework like Bootstrap or Tailwind was used

## 1. Install prerequisites (once)
You need **Node.js** (which includes npm). Download it from
https://nodejs.org/ (the LTS version). Check it worked:
```bash
node --version
npm --version
```

## 2. Install project dependencies
Open a terminal in this `smart-cv-frontend` folder and run:
```bash
npm install
```
This downloads React, Vite, and everything else listed in `package.json`
into a `node_modules` folder (this can take a minute, and you only do it
once — or again if `package.json` changes).

## 3. Run it
```bash
npm run dev
```
Vite will print a local address, usually:
```
Local:   http://localhost:5173/
```
Open that link in your browser — that's your working prototype, running
entirely on your own machine.

## 4. For your presentation
- Live demo: just run `npm run dev` and present from the browser tab.
- No internet connection is needed once `npm install` has been run once.
- If you want a shareable link instead of running it locally every time,
  that's a separate step (deployment) — ask if you want help with that.

## Project structure
```
smart-cv-frontend/
  index.html              # HTML entry point
  package.json             # dependencies + run scripts
  vite.config.js            # Vite/React build config
  src/
    main.jsx                 # mounts the app into index.html
    SmartCVPrototype.jsx      # the entire prototype (all pages, all styling)
```

## Next step
This prototype uses fake/placeholder data and isn't connected to anything.
Once you're ready to move from prototype to a real working system, we'll
connect this to the FastAPI backend (already scaffolded separately) so
login, CV upload, and job matches use real data instead of placeholders.
