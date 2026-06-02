const playerProfiles = {
  sinner: { elo: 2148, rank: 2, serve: 0.684, return: 0.412, clay: 0.66, hard: 0.76, grass: 0.68 },
  alcaraz: { elo: 2182, rank: 1, serve: 0.671, return: 0.426, clay: 0.79, hard: 0.72, grass: 0.73 },
  zverev: { elo: 2055, rank: 3, serve: 0.663, return: 0.391, clay: 0.71, hard: 0.68, grass: 0.58 },
  djokovic: { elo: 2110, rank: 5, serve: 0.666, return: 0.421, clay: 0.72, hard: 0.78, grass: 0.80 },
  swiatek: { elo: 2135, rank: 1, serve: 0.629, return: 0.468, clay: 0.83, hard: 0.72, grass: 0.61 },
  sabalenka: { elo: 2094, rank: 2, serve: 0.653, return: 0.418, clay: 0.68, hard: 0.76, grass: 0.64 },
  gauff: { elo: 2028, rank: 4, serve: 0.617, return: 0.441, clay: 0.69, hard: 0.71, grass: 0.62 },
  keys: { elo: 1945, rank: 12, serve: 0.641, return: 0.394, clay: 0.61, hard: 0.67, grass: 0.66 }
};

const form = document.querySelector("#match-form");
const results = document.querySelector("#results");

function titleCase(value) {
  return value
    .trim()
    .split(/\s+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function profileFor(name, tour) {
  const key = name.trim().toLowerCase().split(/\s+/).pop();
  if (playerProfiles[key]) return playerProfiles[key];

  let seed = 0;
  for (const char of key) seed += char.charCodeAt(0);
  const tourOffset = tour === "WTA" ? -24 : 0;
  return {
    elo: 1740 + tourOffset + (seed % 340),
    rank: 8 + (seed % 84),
    serve: 0.59 + ((seed % 88) / 1000),
    return: 0.36 + ((seed % 72) / 1000),
    clay: 0.52 + ((seed % 34) / 100),
    hard: 0.52 + (((seed + 13) % 34) / 100),
    grass: 0.50 + (((seed + 29) % 30) / 100)
  };
}

function logistic(score) {
  return 1 / (1 + Math.exp(-score));
}

function selected(name) {
  return document.querySelector(`input[name="${name}"]:checked`).value;
}

function pct(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function signed(value, suffix = "") {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(value % 1 === 0 ? 0 : 1)}${suffix}`;
}

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function runPrediction() {
  results.hidden = false;

  const p1Input = document.querySelector("#player-one").value || "Player 1";
  const p2Input = document.querySelector("#player-two").value || "Player 2";
  const p1Name = titleCase(p1Input);
  const p2Name = titleCase(p2Input);
  const surface = selected("surface");
  const tour = selected("tour");
  const format = selected("format");
  const slam = selected("slam");

  const p1 = profileFor(p1Name, tour);
  const p2 = profileFor(p2Name, tour);
  const surfaceKey = surface.toLowerCase();

  const eloDiff = p1.elo - p2.elo;
  const rankSignal = p2.rank - p1.rank;
  const surfaceForm = (p1[surfaceKey] - p2[surfaceKey]) * 100;
  const serveReturn = (p1.serve + p1.return - p2.serve - p2.return) * 100;
  const slamSurface = slam === "Roland Garros" ? "Clay" : slam === "Wimbledon" ? "Grass" : "";
  const slamBoost = slamSurface === surface ? surfaceForm * 0.018 : 0;
  const formatBoost = format === "5" ? eloDiff / 900 : 0;
  const score = eloDiff / 410 + rankSignal / 85 + surfaceForm / 18 + serveReturn / 15 + slamBoost + formatBoost;
  const p1Prob = Math.min(0.91, Math.max(0.09, logistic(score)));
  const p2Prob = 1 - p1Prob;
  const slamLabel = slam === "None" ? "" : ` - ${slam}`;

  setText("#match-title", `${p1Name} vs ${p2Name}`);
  setText("#match-badge", `${tour} - ${surface} - Bo${format}${slamLabel}`);
  setText("#p1-name", p1Name);
  setText("#p2-name", p2Name);
  setText("#p1-prob", pct(p1Prob));
  setText("#p2-prob", pct(p2Prob));
  setText("#elo-diff", signed(eloDiff));
  setText("#surface-form", signed(surfaceForm, "%"));
  setText("#rank-signal", signed(rankSignal));
  setText("#slam-boost", signed(slamBoost * 100, "%"));

  document.querySelector("#p1-bar").style.width = pct(p1Prob);
  document.querySelector("#p2-bar").style.width = pct(p2Prob);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runPrediction();
});
