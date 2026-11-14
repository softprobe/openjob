const state = {
  ui: window.OpenJobUI.preferred(),
  kind: "all",
  q: "",
  location: "",
  remote: "any",
  language: "any",
  tag: "any",
};

const els = {
  kicker: document.querySelector("#kicker"),
  deck: document.querySelector("#deck"),
  tabs: [...document.querySelectorAll(".tab")],
  q: document.querySelector("#q"),
  location: document.querySelector("#location"),
  remote: document.querySelector("#remote"),
  language: document.querySelector("#language"),
  tag: document.querySelector("#tag"),
  count: document.querySelector("#count"),
  results: document.querySelector("#results"),
  footer: document.querySelector("#footer-note"),
};

let posts = [];
let loadError = false;

function t() {
  return OpenJobUI.strings[state.ui] || OpenJobUI.strings.en;
}

function readQuery() {
  const params = new URLSearchParams(location.search);
  const kind = params.get("kind");
  if (kind && ["all", "job", "talent", "company"].includes(kind)) state.kind = kind;
  state.q = params.get("q") || "";
  state.location = params.get("location") || "";
  state.remote = params.get("remote") || "any";
  state.language = params.get("language") || "any";
  state.tag = params.get("tag") || "any";
}

function writeQuery() {
  const params = new URLSearchParams();
  if (state.kind !== "all") params.set("kind", state.kind);
  if (state.q) params.set("q", state.q);
  if (state.location) params.set("location", state.location);
  if (state.remote !== "any") params.set("remote", state.remote);
  if (state.language !== "any") params.set("language", state.language);
  if (state.tag !== "any") params.set("tag", state.tag);
  const next = params.toString();
  const hash = location.hash || "";
  const nextUrl = next ? `?${next}${hash}` : `${location.pathname}${hash}`;
  history.replaceState(null, "", nextUrl);
}

function applyChrome() {
  const copy = t();
  OpenJobUI.apply(state.ui);
  els.kicker.textContent = copy.kicker;
  els.deck.textContent = copy.deck;
  document.querySelector("#label-q").textContent = copy.q;
  document.querySelector("#label-location").textContent = copy.location;
  document.querySelector("#label-remote").textContent = copy.remote;
  document.querySelector("#label-language").textContent = copy.language;
  document.querySelector("#label-tag").textContent = copy.tag;
  els.q.placeholder = copy.q;
  els.location.placeholder = copy.location;
  els.tabs.forEach((button) => {
    button.textContent = copy.tabs[button.dataset.kind];
    button.setAttribute("aria-pressed", button.dataset.kind === state.kind ? "true" : "false");
  });
  els.footer.textContent = copy.footer;
  fillSelect(els.remote, ["any", "remote", "hybrid", "onsite"], (value) =>
    value === "any" ? copy.any : copy.remoteOpt[value]
  );
  const languages = ["any", ...unique(posts.flatMap((post) => post.languages || []))];
  fillSelect(els.language, languages, (value) => (value === "any" ? copy.any : value));
  const tags = ["any", ...unique(posts.flatMap((post) => post.tags || [])).sort()];
  fillSelect(els.tag, tags, (value) => (value === "any" ? copy.any : value));
  els.q.value = state.q;
  els.location.value = state.location;
  paintAgent();
}

function fillSelect(select, values, label) {
  const current = select.value || state[select.id];
  select.replaceChildren();
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label(value);
    select.appendChild(option);
  });
  if (values.includes(current)) select.value = current;
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function haystack(post) {
  return [
    post.title,
    post.headline,
    post.org,
    post.role,
    post.location,
    post.excerpt,
    post.compensation,
    post.owner,
    ...(post.tags || []),
    ...(post.open_to || []),
  ]
    .join("\n")
    .toLowerCase();
}

function matches(post) {
  if (state.kind === "job" && post.kind !== "job") return false;
  if (state.kind === "company" && post.kind !== "company") return false;
  if (state.kind === "talent" && post.kind !== "talent" && post.kind !== "talent-ref") return false;
  if (state.remote !== "any" && post.remote !== state.remote) return false;
  if (state.language !== "any" && !(post.languages || []).includes(state.language)) return false;
  if (state.tag !== "any" && !(post.tags || []).includes(state.tag)) return false;
  if (state.location && !(post.location || "").toLowerCase().includes(state.location.toLowerCase())) return false;
  if (state.q && !haystack(post).includes(state.q.toLowerCase())) return false;
  return true;
}

function render() {
  applyChrome();
  paint({ scroll: true });
}

function entryPath(post) {
  return String(post.path || "").replace(/\.md$/, "");
}

function targetPath() {
  const raw = location.hash.startsWith("#") ? location.hash.slice(1) : "";
  if (!raw) return "";
  try {
    return decodeURIComponent(raw);
  } catch (error) {
    return raw;
  }
}

const QUICKSTART = "https://github.com/softprobe/openjob";

function filtersActive() {
  return Boolean(
    state.q ||
      state.location ||
      state.remote !== "any" ||
      state.language !== "any" ||
      state.tag !== "any"
  );
}

function emptyState() {
  const copy = t();
  const box = document.createElement("div");
  box.id = "post-list";
  box.className = "empty";
  const note = document.createElement("p");
  if (filtersActive()) {
    note.textContent = copy.empty;
    box.appendChild(note);
    return box;
  }
  const leads = copy.emptyLead || {};
  note.textContent = leads[state.kind] || leads.all;
  box.appendChild(note);
  const actions = document.createElement("p");
  actions.className = "empty-actions";
  const postJob = document.createElement("a");
  postJob.href = `${QUICKSTART}#post-a-job-in-2-minutes`;
  postJob.textContent = copy.postJob;
  const addProfile = document.createElement("a");
  addProfile.href = `${QUICKSTART}#add-your-profile`;
  addProfile.textContent = copy.addProfile;
  if (state.kind === "talent") {
    actions.append(addProfile);
  } else if (state.kind === "job") {
    actions.append(postJob);
  } else {
    actions.append(postJob, document.createTextNode(" · "), addProfile);
  }
  box.appendChild(actions);
  return box;
}

function paint(options = {}) {
  if (loadError) {
    els.count.textContent = "";
    if (!document.getElementById("post-list")) {
      els.results.replaceChildren();
      const note = document.createElement("p");
      note.className = "empty";
      note.textContent = t().missing;
      els.results.appendChild(note);
    }
    return;
  }
  els.results.replaceChildren();
  const target = targetPath();
  let visible = posts.filter(matches).slice(0, 200);
  if (target) {
    const pinned = posts.find((post) => entryPath(post) === target);
    if (pinned && !visible.some((post) => post.path === pinned.path)) {
      visible = [pinned, ...visible].slice(0, 200);
    }
  }
  els.count.textContent = t().count(visible.length, posts.length);
  if (!visible.length) {
    els.results.appendChild(emptyState());
    return;
  }
  const list = document.createElement("div");
  visible.forEach((post) => list.appendChild(card(post, target)));
  els.results.appendChild(list);
  if (options.scroll && target) {
    const node = document.getElementById(target);
    if (node) node.scrollIntoView({ block: "start" });
  }
}

function card(post, target) {
  const copy = t();
  const article = document.createElement("article");
  const path = entryPath(post);
  if (path) article.id = path;
  if (path && path === target) article.classList.add("is-target");
  const top = document.createElement("div");
  top.className = "row";
  const badges = document.createElement("div");
  badges.className = "badges";
  const kindKey = post.kind === "talent-ref" ? "talent" : post.kind;
  badges.append(badge((copy.kind && copy.kind[kindKey]) || kindKey));
  if (post.remote && post.remote !== "unspecified") {
    badges.append(badge(copy.remoteOpt[post.remote] || post.remote));
  }
  (post.languages || []).forEach((language) => badges.appendChild(badge(language)));
  if (post.federated) badges.appendChild(badge(copy.federated, "federated"));
  top.appendChild(badges);
  article.appendChild(top);

  const logo = logoImage(post);
  const heading = document.createElement("h2");
  if (post.path && post.permalink) {
    const link = document.createElement("a");
    link.href = `p/${entryPath(post)}/`;
    link.textContent = post.title;
    heading.appendChild(link);
  } else {
    heading.textContent = post.title;
  }
  if (logo) {
    const titleRow = document.createElement("div");
    titleRow.className = "title-row";
    titleRow.append(logo, heading);
    article.appendChild(titleRow);
  } else {
    article.appendChild(heading);
  }

  const bits = [
    post.headline,
    post.location,
    post.org && post.org !== post.headline && post.org !== post.title ? post.org : "",
    post.compensation,
  ]
    .filter(Boolean)
    .filter((value, index, all) => all.indexOf(value) === index);
  if (post.open_to && post.open_to.length) {
    const labels = post.open_to.map((value) => (copy.openTo && copy.openTo[value]) || value);
    bits.push(labels.join(" · "));
  }
  if (bits.length) {
    const sub = document.createElement("p");
    sub.className = "sub";
    sub.textContent = bits.join(" · ");
    article.appendChild(sub);
  }
  if (post.excerpt) {
    const excerpt = document.createElement("p");
    excerpt.className = "excerpt";
    excerpt.textContent = post.excerpt;
    article.appendChild(excerpt);
  }
  if (post.tags && post.tags.length) {
    const tags = document.createElement("ul");
    tags.className = "tags";
    post.tags.forEach((tag) => {
      const item = document.createElement("li");
      item.textContent = tag;
      tags.appendChild(item);
    });
    article.appendChild(tags);
  }
  const applyHow = applyHowBlock(post, copy);
  if (applyHow) article.appendChild(applyHow);
  if (post.kind === "talent" || post.kind === "talent-ref") {
    const reach = document.createElement("p");
    reach.className = "reach";
    reach.textContent = copy.reachNote;
    article.appendChild(reach);
  }
  const links = document.createElement("div");
  links.className = "links";
  if (post.kind === "company") {
    const action = safeLink(post.url, copy.website);
    if (action) links.appendChild(action);
  } else if (post.kind === "talent" || post.kind === "talent-ref") {
    talentLinks(post, copy).forEach((node) => links.appendChild(node));
  }
  const source = safeLink(post.source_url, copy.source);
  if (source) links.appendChild(source);
  const dates = document.createElement("span");
  dates.className = "sub";
  dates.textContent = post.expires
    ? `${copy.posted} ${post.posted} · ${copy.expires} ${post.expires}`
    : `${copy.posted} ${post.posted}`;
  links.appendChild(dates);
  article.appendChild(links);
  if (post.permalink) article.appendChild(shareBlock(post, path === target));
  return article;
}

function shareBlock(post, open) {
  const copy = t();
  const details = document.createElement("details");
  details.className = "share";
  details.open = Boolean(open);
  details.dataset.permalink = post.permalink;
  details.dataset.shareText = post.share_text || "";
  const summary = document.createElement("summary");
  summary.textContent = copy.share;
  details.appendChild(summary);
  const blurb = document.createElement("p");
  blurb.className = "share-text";
  blurb.textContent = post.share_text || "";
  details.appendChild(blurb);
  const note = document.createElement("p");
  note.className = "sub";
  note.textContent = copy.shareNote;
  details.appendChild(note);
  const row = document.createElement("div");
  row.className = "share-links";
  (post.shares || []).forEach((item) => {
    if (!item || !item.href || !/^https:\/\//.test(item.href)) return;
    const link = document.createElement("a");
    link.href = item.href;
    link.textContent = item.label;
    link.rel = "noopener noreferrer";
    link.target = "_blank";
    row.appendChild(link);
  });
  const copyButton = document.createElement("button");
  copyButton.type = "button";
  copyButton.dataset.copy = "";
  copyButton.dataset.done = copy.copied;
  copyButton.textContent = copy.copy;
  row.appendChild(copyButton);
  const wechat = document.createElement("button");
  wechat.type = "button";
  wechat.dataset.wechat = "";
  wechat.setAttribute("aria-expanded", "false");
  wechat.textContent = copy.wechat;
  row.appendChild(wechat);
  details.appendChild(row);
  const field = document.createElement("label");
  field.className = "permalink-label";
  const caption = document.createElement("span");
  caption.className = "sub";
  caption.textContent = copy.permalink;
  const input = document.createElement("input");
  input.className = "permalink";
  input.readOnly = true;
  input.value = post.permalink;
  field.append(caption, input);
  details.appendChild(field);
  const panel = document.createElement("div");
  panel.className = "qr-panel";
  panel.hidden = true;
  const canvas = document.createElement("canvas");
  canvas.setAttribute("aria-label", copy.qrLabel);
  const help = document.createElement("p");
  help.className = "sub";
  help.textContent = copy.wechatHelp;
  panel.append(canvas, help);
  details.appendChild(panel);
  return details;
}

function badge(text, extra) {
  const node = document.createElement("span");
  node.className = extra ? `badge ${extra}` : "badge";
  node.textContent = text;
  return node;
}

function applyHowBlock(post, copy) {
  if (post.kind !== "job") return null;
  const guide = isProfileGuide(post.apply);
  const https = guide ? null : safeLink(post.apply, copy.apply);
  const email = mailLink(post.apply_email, copy.applyEmail);
  if (!https && !email && !guide) return null;
  const box = document.createElement("div");
  box.className = "apply-how";
  if (https || email) {
    const heading = document.createElement("p");
    heading.className = "kicker";
    heading.textContent = copy.howToApply;
    box.appendChild(heading);
  }
  const actions = document.createElement("div");
  actions.className = "apply-actions";
  if (email) {
    const address = document.createElement("p");
    address.className = "apply-address";
    address.textContent = emailAddress(post.apply_email);
    box.appendChild(address);
    actions.appendChild(email);
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.textContent = copy.copyEmail;
    copyButton.addEventListener("click", () => {
      copyAddress(copyButton, address.textContent, copy.copied);
    });
    actions.appendChild(copyButton);
  }
  if (https) actions.appendChild(https);
  if (https || email) box.appendChild(actions);
  if (guide) box.appendChild(profileInvite(copy));
  return box;
}

function profileInvite(copy) {
  const note = document.createElement("p");
  note.className = "also-profile";
  const link = document.createElement("a");
  link.href = `${QUICKSTART}#add-your-profile`;
  link.textContent = copy.alsoProfile;
  note.appendChild(link);
  return note;
}

function talentLinks(post, copy) {
  const links = [];
  if (githubLogin(post.owner)) {
    const github = safeLink(`https://github.com/${post.owner}`, copy.github);
    if (github) links.push(github);
  }
  const linkedin = safeLink(post.linkedin, copy.linkedin);
  if (linkedin) links.push(linkedin);
  const website = safeLink(post.website, copy.website);
  if (website) links.push(website);
  return links;
}

function githubLogin(value) {
  return typeof value === "string" && /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/.test(value);
}

function isProfileGuide(url) {
  if (!url || !String(url).startsWith("https://") || /\s/.test(url)) return false;
  let parsed;
  try {
    parsed = new URL(url);
  } catch (error) {
    return false;
  }
  const fragment = (parsed.hash || "").replace(/^#/, "").toLowerCase();
  if (fragment === "add-your-profile" || fragment === "post-your-resume-talent") return true;
  const host = parsed.hostname.toLowerCase();
  const path = parsed.pathname.replace(/\/$/, "").toLowerCase();
  if ((host === "github.com" || host === "www.github.com") &&
      (path === "/softprobe/openjob" || path.startsWith("/softprobe/openjob/"))) {
    return true;
  }
  let board;
  try {
    board = new URL(boardOrigin());
  } catch (error) {
    return false;
  }
  if (host !== board.hostname.toLowerCase()) return false;
  const prefix = board.pathname.replace(/\/$/, "");
  return parsed.pathname.replace(/\/$/, "") === prefix || parsed.pathname.startsWith(`${prefix}/`);
}

function emailAddress(url) {
  const match = /^mailto:([^\s?]+)$/i.exec(url || "");
  return match ? match[1] : "";
}

function copyAddress(button, text, doneLabel) {
  const previous = button.textContent;
  const finish = () => {
    button.textContent = doneLabel;
    window.setTimeout(() => {
      button.textContent = previous;
    }, 1600);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(finish).catch(finish);
    return;
  }
  finish();
}

function logoImage(post) {
  if (!post.logo || !/^https:\/\/\S+$/.test(post.logo)) return null;
  if (post.kind !== "company" && post.kind !== "job") return null;
  const img = document.createElement("img");
  img.className = "logo";
  img.alt = post.kind === "job" ? post.org || post.title || "" : post.title || "";
  img.width = 48;
  img.height = 48;
  img.referrerPolicy = "no-referrer";
  img.src = post.logo;
  return img;
}

function mailLink(url, text) {
  if (!url || !/^mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/i.test(url)) return null;
  const link = document.createElement("a");
  link.href = url;
  link.textContent = text;
  link.rel = "nofollow noopener noreferrer";
  return link;
}

function safeLink(url, text) {
  if (!url || !/^https:\/\//.test(url)) return null;
  const link = document.createElement("a");
  link.href = url;
  link.textContent = text;
  link.rel = "noopener noreferrer";
  link.target = "_blank";
  return link;
}

const AGENT_NEW = {
  job: "https://github.com/softprobe/openjob/new/main/jobs",
  talent: "https://github.com/softprobe/openjob/new/main/talents",
  company: "https://github.com/softprobe/openjob/new/main/companies",
};

let agentKind = "find";
let audienceChoice = "";
let agentTouched = false;

function boardOrigin() {
  const canonical = document.querySelector('link[rel="canonical"]');
  const href = canonical && canonical.getAttribute("href");
  if (!href) return "https://softprobe.github.io/openjob/";
  return href.endsWith("/") ? href : `${href}/`;
}

function agentForFilter(kind) {
  if (audienceChoice === "hiring") return "job";
  if (audienceChoice === "looking") return "talent";
  if (kind === "job") return "talent";
  if (kind === "company") return "company";
  if (kind === "talent") {
    const anyTalent = posts.some((post) => post.kind === "talent" || post.kind === "talent-ref");
    return anyTalent ? "job" : "talent";
  }
  return "find";
}

function agentPrompt(kind) {
  const copy = t();
  const prompts = copy.agentPrompt || {};
  const writer = prompts[kind] || prompts.find || prompts.job;
  if (typeof writer === "function") return writer(boardOrigin());
  return String(writer || "");
}

function paintAgent() {
  const copy = t();
  const prompt = document.querySelector("#agent-prompt");
  const link = document.querySelector("#agent-new-link");
  const finding = agentKind === "find";
  if (prompt) prompt.textContent = agentPrompt(agentKind);
  if (link) link.href = AGENT_NEW[agentKind] || AGENT_NEW.talent;
  document.querySelectorAll("[data-agent]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.agent === agentKind ? "true" : "false");
  });
  document.querySelectorAll("[data-agent-find]").forEach((node) => {
    node.hidden = !finding;
  });
  document.querySelectorAll("[data-agent-create]").forEach((node) => {
    node.hidden = finding;
  });
  const fallback = document.querySelector("[data-agent-find].agent-fallback");
  if (fallback) fallback.textContent = copy.agentFindFallback;
  const createFallback = document.querySelector("[data-agent-create].agent-fallback");
  if (createFallback) createFallback.textContent = copy.agentFallback;
  document.querySelectorAll("[data-audience]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.audience === audienceChoice ? "true" : "false");
  });
}

function bindAgent() {
  const root = document.querySelector("#agent");
  if (!root) return;
  root.querySelectorAll("[data-agent]").forEach((button) => {
    button.addEventListener("click", () => {
      agentTouched = true;
      agentKind = button.dataset.agent || "find";
      paintAgent();
    });
  });
  const copyButton = document.querySelector("#agent-copy");
  const prompt = document.querySelector("#agent-prompt");
  if (copyButton && prompt) {
    copyButton.addEventListener("click", () => {
      copyAddress(copyButton, prompt.textContent, t().agentCopied);
    });
  }
  paintAgent();
}

function bindAudience() {
  document.querySelectorAll("[data-audience]").forEach((button) => {
    button.addEventListener("click", () => {
      audienceChoice = button.dataset.audience === "hiring" ? "hiring" : "looking";
      state.kind = audienceChoice === "hiring" ? "talent" : "job";
      agentTouched = true;
      agentKind = agentForFilter(state.kind);
      const details = document.querySelector("#agent");
      if (details) details.open = true;
      writeQuery();
      render();
    });
  });
}

function bind() {
  document.addEventListener("openjob-ui", (event) => {
    state.ui = event.detail === "zh" ? "zh" : "en";
    writeQuery();
    render();
  });
  els.tabs.forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.kind !== state.kind) audienceChoice = "";
      state.kind = button.dataset.kind;
      agentTouched = true;
      agentKind = agentForFilter(state.kind);
      writeQuery();
      render();
    });
  });
  const sync = () => {
    state.q = els.q.value.trim();
    state.location = els.location.value.trim();
    state.remote = els.remote.value;
    state.language = els.language.value;
    state.tag = els.tag.value;
    writeQuery();
    paint();
  };
  ["input", "change"].forEach((eventName) => {
    els.q.addEventListener(eventName, sync);
    els.location.addEventListener(eventName, sync);
    els.remote.addEventListener(eventName, sync);
    els.language.addEventListener(eventName, sync);
    els.tag.addEventListener(eventName, sync);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement.tagName !== "INPUT") {
      event.preventDefault();
      els.q.focus();
    }
  });
  window.addEventListener("hashchange", () => paint({ scroll: true }));
}

async function main() {
  readQuery();
  bind();
  bindAgent();
  bindAudience();
  try {
    const response = await fetch("./index.json");
    if (!response.ok) throw new Error(String(response.status));
    const documentIndex = await response.json();
    posts = documentIndex.posts || [];
  } catch (error) {
    loadError = true;
  }
  if (!agentTouched) agentKind = agentForFilter(state.kind);
  render();
}

main();
