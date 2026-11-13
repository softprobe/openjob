const STRINGS = {
  en: {
    kicker: "GitHub-native classifieds",
    deck: "Jobs and talent profiles, published as pull requests. No accounts. No phone numbers.",
    lang: "中文",
    tabs: { all: "All", job: "Jobs", talent: "Talent", company: "Companies" },
    q: "Role, skill, or keyword",
    location: "Location",
    remote: "Remote",
    language: "Language",
    tag: "Tag",
    examples: "Show samples",
    any: "Any",
    remoteOpt: { remote: "Remote", onsite: "On-site", hybrid: "Hybrid", unspecified: "Not set" },
    count: (n, total) => `${n} shown of ${total}`,
    empty: "Nothing matches these filters.",
    missing: "The index is not here yet. GitHub Pages builds it from the posts. Locally, from the repo root: python -m validator build-index --root . --out site/index.json",
    sample: "Sample",
    federated: "Own repo",
    apply: "Apply",
    website: "Website",
    profile: "Profile",
    source: "Source",
    posted: "Posted",
    expires: "Expires",
    footer: "Contact is a link, not a phone number or an email address. Posts are CC BY 4.0. Code is MIT.",
  },
  zh: {
    kicker: "用 Pull Request 发布的分类信息",
    deck: "职位和人才档案都通过 Pull Request 发布。没有账号系统，也不收集电话。",
    lang: "EN",
    tabs: { all: "全部", job: "职位", talent: "人才", company: "公司" },
    q: "职位、技能或关键词",
    location: "地点",
    remote: "远程",
    language: "语言",
    tag: "标签",
    examples: "显示示例",
    any: "不限",
    remoteOpt: { remote: "远程", onsite: "到岗", hybrid: "混合", unspecified: "未标明" },
    count: (n, total) => `显示 ${n} / ${total}`,
    empty: "没有符合这些条件的帖子。",
    missing: "索引还没生成。GitHub Pages 会根据帖子构建。本地在仓库根目录运行：python -m validator build-index --root . --out site/index.json",
    sample: "示例",
    federated: "独立仓库",
    apply: "申请",
    website: "网站",
    profile: "档案",
    source: "源文件",
    posted: "发布",
    expires: "到期",
    footer: "联系方式是链接，不是电话或邮箱。帖子以 CC BY 4.0 授权，代码以 MIT 授权。",
  },
};

const state = {
  ui: localStorage.getItem("openjob-ui") === "zh" ? "zh" : "en",
  kind: "all",
  q: "",
  location: "",
  remote: "any",
  language: "any",
  tag: "any",
  examples: true,
};

const els = {
  kicker: document.querySelector("#kicker"),
  deck: document.querySelector("#deck"),
  lang: document.querySelector("#lang"),
  tabs: [...document.querySelectorAll(".tab")],
  q: document.querySelector("#q"),
  location: document.querySelector("#location"),
  remote: document.querySelector("#remote"),
  language: document.querySelector("#language"),
  tag: document.querySelector("#tag"),
  examples: document.querySelector("#examples"),
  count: document.querySelector("#count"),
  results: document.querySelector("#results"),
  footer: document.querySelector("#footer-note"),
};

let posts = [];
let loadError = false;

function t() {
  return STRINGS[state.ui];
}

function readQuery() {
  const params = new URLSearchParams(location.search);
  if (params.get("ui") === "zh" || params.get("ui") === "en") state.ui = params.get("ui");
  const kind = params.get("kind");
  if (kind && ["all", "job", "talent", "company"].includes(kind)) state.kind = kind;
  state.q = params.get("q") || "";
  state.location = params.get("location") || "";
  state.remote = params.get("remote") || "any";
  state.language = params.get("language") || "any";
  state.tag = params.get("tag") || "any";
  if (params.get("examples") === "0") state.examples = false;
}

function writeQuery() {
  const params = new URLSearchParams();
  if (state.ui !== "en") params.set("ui", state.ui);
  if (state.kind !== "all") params.set("kind", state.kind);
  if (state.q) params.set("q", state.q);
  if (state.location) params.set("location", state.location);
  if (state.remote !== "any") params.set("remote", state.remote);
  if (state.language !== "any") params.set("language", state.language);
  if (state.tag !== "any") params.set("tag", state.tag);
  if (!state.examples) params.set("examples", "0");
  const next = params.toString();
  history.replaceState(null, "", next ? `?${next}` : location.pathname);
}

function applyChrome() {
  const copy = t();
  document.documentElement.lang = state.ui === "zh" ? "zh" : "en";
  els.kicker.textContent = copy.kicker;
  els.deck.textContent = copy.deck;
  els.lang.textContent = copy.lang;
  els.lang.setAttribute("aria-pressed", state.ui === "zh" ? "true" : "false");
  document.querySelector("#label-q").textContent = copy.q;
  document.querySelector("#label-location").textContent = copy.location;
  document.querySelector("#label-remote").textContent = copy.remote;
  document.querySelector("#label-language").textContent = copy.language;
  document.querySelector("#label-tag").textContent = copy.tag;
  document.querySelector("#label-examples").textContent = copy.examples;
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
  els.examples.checked = state.examples;
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
  if (!state.examples && post.example) return false;
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
  paint();
}

function paint() {
  els.results.replaceChildren();
  if (loadError) {
    els.count.textContent = "";
    const note = document.createElement("p");
    note.className = "empty";
    note.textContent = t().missing;
    els.results.appendChild(note);
    return;
  }
  const visible = posts.filter(matches).slice(0, 200);
  els.count.textContent = t().count(visible.length, posts.length);
  if (!visible.length) {
    els.results.appendChild(Object.assign(document.createElement("p"), { className: "empty", textContent: t().empty }));
    return;
  }
  const list = document.createElement("div");
  visible.forEach((post) => list.appendChild(card(post)));
  els.results.appendChild(list);
}

function card(post) {
  const copy = t();
  const article = document.createElement("article");
  const top = document.createElement("div");
  top.className = "row";
  const badges = document.createElement("div");
  badges.className = "badges";
  const kindKey = post.kind === "talent-ref" ? "talent" : post.kind;
  badges.append(badge(copy.tabs[kindKey] || kindKey));
  if (post.remote && post.remote !== "unspecified") {
    badges.append(badge(copy.remoteOpt[post.remote] || post.remote));
  }
  (post.languages || []).forEach((language) => badges.appendChild(badge(language)));
  if (post.example) badges.appendChild(badge(copy.sample, "sample"));
  if (post.federated) badges.appendChild(badge(copy.federated, "federated"));
  top.appendChild(badges);
  article.appendChild(top);

  const heading = document.createElement("h2");
  const primary = safeLink(post.url, post.title);
  if (primary) heading.appendChild(primary);
  else heading.textContent = post.title;
  article.appendChild(heading);

  const bits = [
    post.headline,
    post.location,
    post.org && post.org !== post.headline && post.org !== post.title ? post.org : "",
    post.compensation,
  ]
    .filter(Boolean)
    .filter((value, index, all) => all.indexOf(value) === index);
  if (post.open_to && post.open_to.length) bits.push(post.open_to.join(" · "));
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
  const links = document.createElement("div");
  links.className = "links";
  const actionLabel = post.kind === "job" ? copy.apply : post.kind === "company" ? copy.website : copy.profile;
  const action = safeLink(post.url, actionLabel);
  const source = safeLink(post.source_url, copy.source);
  if (action) links.appendChild(action);
  if (source) links.appendChild(source);
  const dates = document.createElement("span");
  dates.className = "sub";
  dates.textContent = post.expires
    ? `${copy.posted} ${post.posted} · ${copy.expires} ${post.expires}`
    : `${copy.posted} ${post.posted}`;
  links.appendChild(dates);
  article.appendChild(links);
  return article;
}

function badge(text, extra) {
  const node = document.createElement("span");
  node.className = extra ? `badge ${extra}` : "badge";
  node.textContent = text;
  return node;
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

function bind() {
  els.lang.addEventListener("click", () => {
    state.ui = state.ui === "en" ? "zh" : "en";
    localStorage.setItem("openjob-ui", state.ui);
    writeQuery();
    render();
  });
  els.tabs.forEach((button) => {
    button.addEventListener("click", () => {
      state.kind = button.dataset.kind;
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
    state.examples = els.examples.checked;
    writeQuery();
    paint();
  };
  ["input", "change"].forEach((eventName) => {
    els.q.addEventListener(eventName, sync);
    els.location.addEventListener(eventName, sync);
    els.remote.addEventListener(eventName, sync);
    els.language.addEventListener(eventName, sync);
    els.tag.addEventListener(eventName, sync);
    els.examples.addEventListener(eventName, sync);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement.tagName !== "INPUT") {
      event.preventDefault();
      els.q.focus();
    }
  });
}

async function main() {
  readQuery();
  bind();
  try {
    const response = await fetch("./index.json");
    if (!response.ok) throw new Error(String(response.status));
    const documentIndex = await response.json();
    posts = documentIndex.posts || [];
    render();
  } catch (error) {
    loadError = true;
    render();
  }
}

main();
