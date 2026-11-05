// Builds the GitHub stats and top languages cards shown in the README.
// Runs in a GitHub Action once a day and saves the cards into the stats/ folder.

const fs = require("fs");

const USER = "MichaelKokal";
const TOKEN = process.env.GITHUB_TOKEN;

const colors = {
  bg: "#151515",
  border: "#e4e2e2",
  title: "#ffffff",
  text: "#c9d1d9",
  icon: "#79ff97",
};

async function query(q, variables) {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: { Authorization: `bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ query: q, variables }),
  });
  const json = await res.json();
  if (json.errors) throw new Error(JSON.stringify(json.errors));
  return json.data;
}

async function getData() {
  const repos = [];
  let cursor = null;
  let user;
  do {
    const data = await query(
      `query($login: String!, $cursor: String) {
        user(login: $login) {
          name
          contributionsCollection { totalCommitContributions }
          pullRequests { totalCount }
          issues { totalCount }
          repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
          repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
            pageInfo { hasNextPage endCursor }
            nodes {
              stargazerCount
              languages(first: 10, orderBy: { field: SIZE, direction: DESC }) {
                edges { size node { name color } }
              }
            }
          }
        }
      }`,
      { login: USER, cursor }
    );
    user = data.user;
    repos.push(...user.repositories.nodes);
    cursor = user.repositories.pageInfo.hasNextPage ? user.repositories.pageInfo.endCursor : null;
  } while (cursor);
  return { user, repos };
}

function escape(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Lines fade in and slide from the left one after another, like the neofetch card.
// The animated <g> wraps the positioned one, because a CSS transform would otherwise
// replace the element's own transform attribute.
const ANIMATION = `
    .l { opacity: 0; animation: print .35s ease-out forwards; }
    .grow { transform-box: fill-box; transform-origin: 0 50%; transform: scaleX(0); animation: grow .7s cubic-bezier(.2,.7,.3,1) forwards; }
    @keyframes print { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes grow { to { transform: scaleX(1); } }`;

function line(order, start, inner, cls = "l") {
  return `<g class="${cls}" style="animation-delay:${(start + order * 0.1).toFixed(2)}s">${inner}</g>`;
}

function statsCard(user, repos) {
  const stars = repos.reduce((sum, r) => sum + r.stargazerCount, 0);
  const rows = [
    ["Total Stars Earned", stars],
    [`Commits (${new Date().getFullYear()})`, user.contributionsCollection.totalCommitContributions],
    ["Total PRs", user.pullRequests.totalCount],
    ["Total Issues", user.issues.totalCount],
    ["Contributed to (last year)", user.repositoriesContributedTo.totalCount],
  ];
  const name = user.name || USER;
  const lines = rows
    .map(
      ([label, value], i) => `
    ${line(i + 1, 0.3, `<g transform="translate(25, ${70 + i * 25})">
      <circle cx="6" cy="-5" r="4" fill="${colors.icon}"/>
      <text x="20" y="0" class="label">${escape(label)}:</text>
      <text x="240" y="0" class="value">${value}</text>
    </g>`)}`
    )
    .join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200">
  <style>
    .title { font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: ${colors.title}; }
    .label { font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: ${colors.text}; }
    .value { font: 700 14px 'Segoe UI', Ubuntu, sans-serif; fill: ${colors.text}; }${ANIMATION}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="399" height="199" fill="${colors.bg}" stroke="${colors.border}"/>
  ${line(0, 0.3, `<text x="25" y="35" class="title">${escape(name)}'s GitHub Stats</text>`)}${lines}
</svg>
`;
}

function languagesCard(repos) {
  const totals = {};
  for (const repo of repos) {
    for (const { size, node } of repo.languages.edges) {
      totals[node.name] = totals[node.name] || { size: 0, color: node.color || "#858585" };
      totals[node.name].size += size;
    }
  }
  const top = Object.entries(totals)
    .sort((a, b) => b[1].size - a[1].size)
    .slice(0, 6);
  const sum = top.reduce((s, [, l]) => s + l.size, 0) || 1;

  let x = 0;
  const bar = top
    .map(([, l]) => {
      const w = (l.size / sum) * 350;
      const part = `<rect x="${x}" y="0" width="${w}" height="8" fill="${l.color}"/>`;
      x += w;
      return part;
    })
    .join("");

  const legend = top
    .map(([name, l], i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const pct = ((l.size / sum) * 100).toFixed(2);
      return `
    ${line(i, 1.1, `<g transform="translate(${col * 175}, ${row * 25})">
      <circle cx="5" cy="6" r="5" fill="${l.color}"/>
      <text x="15" y="10" class="lang">${escape(name)} ${pct}%</text>
    </g>`)}`;
    })
    .join("");

  // Same height as the stats card so the two line up side by side
  const height = Math.max(200, 105 + Math.ceil(top.length / 2) * 25);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="${height}" viewBox="0 0 400 ${height}">
  <style>
    .title { font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: ${colors.title}; }
    .lang { font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: ${colors.text}; }${ANIMATION}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="399" height="${height - 1}" fill="${colors.bg}" stroke="${colors.border}"/>
  ${line(0, 0.7, `<text x="25" y="35" class="title">Most Used Languages</text>`)}
  <clipPath id="round"><rect x="0" y="0" width="350" height="8" rx="5"/></clipPath>
  <g transform="translate(25, 55)" clip-path="url(#round)">${line(0, 0.85, bar, "grow")}</g>
  <g transform="translate(25, 80)">${legend}
  </g>
</svg>
`;
}

(async () => {
  const { user, repos } = await getData();
  fs.mkdirSync("stats", { recursive: true });
  fs.writeFileSync("stats/stats.svg", statsCard(user, repos));
  fs.writeFileSync("stats/top-langs.svg", languagesCard(repos));
  console.log("Cards saved to stats/");
})();
