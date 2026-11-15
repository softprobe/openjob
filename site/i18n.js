/* One interface language per visitor.

The static HTML is English, which is what a crawler or a browser without
JavaScript reads. This script switches labels, headings, and buttons. It does
not rewrite a post: job, talent, and company text stays as it was written.

Choice order: a ?ui=en or ?ui=zh link, then the language button's saved
choice in localStorage, then the first preferred language. A tag whose
primary subtag is zh (zh, zh-CN, zh-Hans, zh-TW) selects Chinese. Anything
else, including an empty list, stays English.
*/

(function () {
  var STORAGE_KEY = "openjob-ui";

  var STRINGS = {
    en: {
      kicker: "OpenJob",
      hero: "The open job index for AI agents",
      deck: "Real jobs, linked to the employer's own page, checked daily. Free for everyone.",
      findMe: "Find me a job",
      postRole: "Post our role",
      addMine: "Add my profile",
      byHand: "Do it by hand",
      tabs: { all: "All", job: "Jobs", talent: "Talent", company: "Companies" },
      kind: { job: "Job", talent: "Talent", company: "Company" },
      q: "Role, skill, or keyword",
      location: "Location",
      remote: "Remote",
      language: "Language",
      tag: "Tag",
      origin: "Source",
      originOpt: { all: "All sources", owner: "Posted on OpenJob", indexed: "Indexed" },
      indexedBadge: function (hours) { return "Indexed · checked " + hours + "h ago"; },
      applyOnSite: function (name) { return "Apply on " + name + " site"; },
      any: "Any",
      remoteOpt: { remote: "Remote", onsite: "On-site", hybrid: "Hybrid", unspecified: "Not set" },
      employment: {
        FULL_TIME: "Full-time",
        PART_TIME: "Part-time",
        CONTRACTOR: "Contractor",
        TEMPORARY: "Temporary",
        INTERN: "Intern",
        VOLUNTEER: "Volunteer",
        PER_DIEM: "Per diem",
        OTHER: "Other",
      },
      count: function (n, total) { return n + " shown of " + total; },
      empty: "Nothing matches these filters.",
      emptyLead: {
        all: "No posts yet.",
        job: "No jobs yet.",
        talent: "No profiles yet.",
        company: "No company pages yet.",
      },
      postJob: "Post a job",
      addProfile: "Add your profile",
      looking: "I'm looking for work",
      hiring: "I'm hiring",
      audienceLabel: "Who you are",
      githubAccount: "You need a free GitHub account. You can only edit your own posts.",
      useAgent: "Use your AI agent",
      agentFind: "Find jobs",
      agentJob: "Job",
      agentTalent: "Talent profile",
      agentCompany: "Company",
      agentCopy: "Copy prompt",
      agentCopied: "Copied",
      agentFallback: "If your agent cannot open a pull request, ask it to print the Markdown file. Paste that file with the GitHub new-file link for the folder.",
      agentFindFallback: "This prompt does not open a pull request. The agent reads the public index and returns matching permalinks.",
      agentIndex: "Read the live index",
      agentNew: "Create the file on GitHub",
      agentPrompt: {
        find: function () {
          return "Read https://openjob.softprobe.ai/llms.txt and follow it. If the OpenJob MCP server is connected, call search_jobs. Otherwise GET https://openjob.softprobe.ai/index.json and keep posts whose kind is job. Return each match with its permalink and the apply method already on that post. Do not invent an email or a phone number. Resume or bio: <paste here>";
        },
        talent: function (origin) {
          return "Read " + origin + "llms.txt and follow it. Save the profile as talents/<github-login>.md and set github to that same login. If the OpenJob MCP server is connected, call create_or_update_post with kind talent. Do not include an email, a phone number, or a WeChat ID. Bio: <paste here>";
        },
        job: function (origin) {
          return "Read " + origin + "llms.txt and follow it. If the OpenJob MCP server is connected, call create_or_update_post with kind job. Otherwise open one pull request that adds jobs/YYYY/MM/<company>-<role>.md. Set posted_by to the GitHub login that opens the pull request. If the company page exists, that login must be in its owners list. One post per pull request. Role: <paste here>";
        },
        company: function (origin) {
          return "Read " + origin + "llms.txt and follow it. Turn the details below into an OpenJob company page. Set owners to GitHub logins that include the account opening the pull request, and posted_by to that same login. A new company page is reviewed once. Open one pull request to github.com/softprobe/openjob. Details: <paste here>";
        },
      },
      missing: "The index is not here yet. GitHub Pages builds it from the posts. Locally, from the repo root: python -m validator build-index --root . --out site/index.json",
      federated: "Own repo",
      apply: "Apply",
      applyEmail: "Apply by email",
      howToApply: "How to apply",
      alsoProfile: "Also add your profile",
      copyEmail: "Copy email",
      copied: "Copied",
      website: "Website",
      github: "GitHub",
      linkedin: "LinkedIn",
      profile: "Profile",
      reachNote: "This board does not list an email or a phone number. Reach this person through the GitHub, LinkedIn, or website link.",
      openTo: {
        "full-time": "Full-time",
        "part-time": "Part-time",
        contract: "Contract",
        internship: "Internship",
      },
      source: "Source",
      posted: "Posted",
      expires: "Expires",
      footer: "Phone numbers are not allowed. A job may show Apply by email when the address is on the company domain. Share text never includes a phone number or an email. Posts are CC BY 4.0. Code is MIT.",
      share: "Share",
      shareNote: "The buttons send this text and the permalink. They do not send an apply link, a phone number, or an email address. An Apply by email button on this page is not part of this text.",
      copy: "Copy link",
      wechat: "WeChat",
      wechatHelp: "Scan with WeChat. This code is the permalink, drawn in your browser.",
      wechatPaste: "Copy the link and paste it into WeChat.",
      permalink: "Permalink",
      qrLabel: "QR code for this permalink",
      board: "Board",
      about: "About",
      feed: "Feed",
      jobsFeed: "New jobs",
      talentsFeed: "New profiles",
      skipResults: "Skip to results",
      skipShare: "Skip to share",
      postType: "Post type",
      openJobs: "Open jobs",
      openJobsMore: "The jobs archive lists every open role.",
      previous: "Previous",
      next: "Next",
      pageOf: function (n, pages) { return "Page " + n + " of " + pages; },
      archive: {
        job: function (n) { return "Jobs archive, " + n + " posts"; },
        talent: function (n) { return "Talent archive, " + n + " posts"; },
        company: function (n) { return "Companies archive, " + n + " posts"; },
      },
      notFound: "Not found",
      notFoundBody: "That page is not on the board. It may have expired, or the address may be wrong.",
      back: "Back to the board",
      aboutWhat: "What is OpenJob?",
      aboutWhatBody: "The open job index for AI agents. Real jobs, linked to the employer's own page, checked daily. Free for everyone.",
      aboutPost: "How do I post a job or a talent profile?",
      aboutApply: "How do I apply?",
      aboutApplyBody: "The job page shows the method. That is an email on the company domain, an https link, or both. A link to this board's profile guide is not an application.",
      aboutProfile: "How do I add a profile?",
      aboutProfileBody: "A talent profile is talents/&lt;your-github-name&gt;.md. It is not how you apply to a job. Do not put a phone number or a personal email in that profile. You need a free GitHub account. You can only edit your own posts.",
      aboutFeeds: "How do I hear about new posts?",
      aboutFeedsBody: "New jobs are in jobs.xml. New profiles are in talents.xml. Every post is in feed.xml. The catalog is index.json.",
      aboutPrivacy: "Why are phone numbers and personal emails rejected?",
      aboutPrivacyBody: "The board is public. Phone numbers are never accepted. Talent posts cannot contain an email. A job may list one hiring address, and only when that domain matches the company website.",
      aboutDuration: "How long does a post stay up?",
      aboutLanguages: "Can a post be in English and Chinese?",
      aboutIndex: "How does the index work?",
      aboutIndexBody: "OpenJob reads public job feeds from Greenhouse, Lever, Ashby, and Workable once a day. It stores the title, company, location, department, type, dates, and the link to the employer's page. It does not store the job description or anyone's name. A role that disappears from a healthy feed is closed. A feed that fails stays up for 48 hours and is then hidden. Indexed jobs are labeled and link out. They are not posts on OpenJob, and CC BY does not cover them.",
      aboutClaim: "How does a company claim its page?",
      aboutClaimBody: "Add or edit <code>companies/&lt;letter&gt;/&lt;slug&gt;.md</code> and set <code>owners</code> to the GitHub logins that should control it. Publish <code>https://&lt;company-domain&gt;/.well-known/openjob.txt</code> with one login per line. The checker reads that file. When every owner is listed, the pull request can auto-merge. Otherwise a maintainer reviews it. After a claim, <code>index: \"off\"</code> stops indexing that company's board.",
      aboutOptOut: "How does a company opt out?",
      aboutOptOutBody: "Open a GitHub issue, or a pull request that adds the board to <code>sources/denylist.yml</code>. A maintainer removes it. The aim is to do that within 24 hours. Claiming the page and setting <code>index: \"off\"</code> does the same thing for a company that wants to keep the page.",
      aboutWho: "Who maintains this?",
    },
    zh: {
      kicker: "OpenJob",
      hero: "面向 AI 代理的开放职位索引",
      deck: "真实职位，链到雇主自己的页面，每天检查。对所有人免费。",
      findMe: "帮我找工作",
      postRole: "发布我们的职位",
      addMine: "添加我的档案",
      byHand: "自己动手",
      tabs: { all: "全部", job: "职位", talent: "人才", company: "公司" },
      kind: { job: "职位", talent: "人才", company: "公司" },
      q: "职位、技能或关键词",
      location: "地点",
      remote: "远程",
      language: "语言",
      tag: "标签",
      origin: "来源",
      originOpt: { all: "全部来源", owner: "发布在 OpenJob", indexed: "索引" },
      indexedBadge: function (hours) { return "索引 · " + hours + " 小时前检查"; },
      applyOnSite: function (name) { return "在 " + name + " 的网站申请"; },
      any: "不限",
      remoteOpt: { remote: "远程", onsite: "到岗", hybrid: "混合", unspecified: "未标明" },
      employment: {
        FULL_TIME: "全职",
        PART_TIME: "兼职",
        CONTRACTOR: "合同工",
        TEMPORARY: "临时",
        INTERN: "实习",
        VOLUNTEER: "志愿",
        PER_DIEM: "按日",
        OTHER: "其他",
      },
      count: function (n, total) { return "显示 " + n + " / " + total; },
      empty: "没有符合这些条件的帖子。",
      emptyLead: {
        all: "还没有帖子。",
        job: "还没有职位。",
        talent: "还没有人才档案。",
        company: "还没有公司页。",
      },
      postJob: "发布职位",
      addProfile: "添加档案",
      looking: "我在找工作",
      hiring: "我在招聘",
      audienceLabel: "你是哪一方",
      githubAccount: "你需要一个免费的 GitHub 账号。你只能改自己的帖子。",
      useAgent: "使用你的 AI 助手",
      agentFind: "找职位",
      agentJob: "职位",
      agentTalent: "人才档案",
      agentCompany: "公司",
      agentCopy: "复制提示",
      agentCopied: "已复制",
      agentFallback: "如果助手不能开 Pull Request，让它输出 Markdown 文件，再用下面的 GitHub 新文件链接粘贴进去。",
      agentFindFallback: "这段提示不需要开 Pull Request。助手读取公开索引，并返回匹配的永久链接。",
      agentIndex: "阅读实时索引",
      agentNew: "在 GitHub 上新建文件",
      agentPrompt: {
        find: function () {
          return "阅读 https://openjob.softprobe.ai/llms.txt 并按它执行。如果已连接 OpenJob MCP，调用 search_jobs。否则 GET https://openjob.softprobe.ai/index.json，只保留 kind 为 job 的帖子。每条写出永久链接，以及帖子上已有的申请方式。不要编造邮箱或电话。简历或简介：<粘贴在这里>";
        },
        talent: function (origin) {
          return "阅读 " + origin + "llms.txt 并按它执行。档案保存为 talents/<github-login>.md，github 填同一个登录名。如果已连接 OpenJob MCP，用 kind talent 调用 create_or_update_post。不要写邮箱、电话或微信号。简介：<粘贴在这里>";
        },
        job: function (origin) {
          return "阅读 " + origin + "llms.txt 并按它执行。如果已连接 OpenJob MCP，用 kind job 调用 create_or_update_post。否则开一个 Pull Request，只添加 jobs/YYYY/MM/<company>-<role>.md。posted_by 填开这个 Pull Request 的 GitHub 登录名。公司页已存在时，这个登录名必须在 owners 里。一个 Pull Request 只放一篇帖子。职位：<粘贴在这里>";
        },
        company: function (origin) {
          return "阅读 " + origin + "llms.txt 并按它执行。把下面的内容写成 OpenJob 公司页。owners 要包含开 Pull Request 的登录名，posted_by 也填这个登录名。新公司页会先审核一次。向 github.com/softprobe/openjob 开一个 Pull Request。内容：<粘贴在这里>";
        },
      },
      missing: "索引还没生成。GitHub Pages 会根据帖子构建。本地在仓库根目录运行：python -m validator build-index --root . --out site/index.json",
      federated: "独立仓库",
      apply: "申请",
      applyEmail: "邮件申请",
      howToApply: "如何申请",
      alsoProfile: "也可以添加档案",
      copyEmail: "复制邮箱",
      copied: "已复制",
      website: "网站",
      github: "GitHub",
      linkedin: "LinkedIn",
      profile: "档案",
      reachNote: "看板上不列出邮箱或电话。请通过 GitHub、LinkedIn 或网站链接联系。",
      openTo: {
        "full-time": "全职",
        "part-time": "兼职",
        contract: "合同",
        internship: "实习",
      },
      source: "源文件",
      posted: "发布",
      expires: "到期",
      footer: "不允许电话号码。职位可以在公司域名匹配时显示「邮件申请」。分享文字不含电话或邮箱。帖子以 CC BY 4.0 授权，代码以 MIT 授权。",
      share: "分享",
      shareNote: "按钮只发送这段文字和永久链接，不包含申请链接、电话或邮箱。页面上的「邮件申请」按钮不在这段文字里。",
      copy: "复制链接",
      wechat: "微信",
      wechatHelp: "用微信扫描。二维码是本条永久链接，由浏览器在本地生成。",
      wechatPaste: "复制链接，粘贴到微信。",
      permalink: "永久链接",
      qrLabel: "本条永久链接的二维码",
      board: "公告板",
      about: "关于",
      feed: "订阅",
      jobsFeed: "新职位",
      talentsFeed: "新档案",
      skipResults: "跳到结果",
      skipShare: "跳到分享",
      postType: "帖子类型",
      openJobs: "在招职位",
      openJobsMore: "职位归档列出全部在招职位。",
      previous: "上一页",
      next: "下一页",
      pageOf: function (n, pages) { return "第 " + n + " / " + pages + " 页"; },
      archive: {
        job: function (n) { return "职位归档，" + n + " 篇"; },
        talent: function (n) { return "人才归档，" + n + " 篇"; },
        company: function (n) { return "公司归档，" + n + " 篇"; },
      },
      notFound: "找不到",
      notFoundBody: "这个页面不在看板上。它可能已经到期，或者地址不对。",
      back: "返回看板",
      aboutWhat: "OpenJob 是什么？",
      aboutWhatBody: "面向 AI 代理的开放职位索引。真实职位，链到雇主自己的页面，每天检查。对所有人免费。",
      aboutPost: "如何发布职位或人才档案？",
      aboutPostBody: "把模板复制到 <code>jobs/</code>、<code>talents/</code> 或 <code>companies/</code>，然后开 Pull Request。只改帖子的请求会在检查通过后自动合并。",
      aboutApply: "如何申请？",
      aboutApplyBody: "申请方式写在职位页上，是公司域名上的邮箱、一个 https 链接，或两者都有。指向本看板档案说明的链接不是申请方式。",
      aboutProfile: "如何添加档案？",
      aboutProfileBody: "人才档案是 <code>talents/&lt;你的-github-用户名&gt;.md</code>。这不是申请某个职位的方式。不要写电话或个人邮箱。你需要一个免费的 GitHub 账号。你只能改自己的帖子。步骤见 <a href=\"https://github.com/softprobe/openjob#add-your-profile\">添加档案</a>。",
      aboutFeeds: "如何知道有新帖子？",
      aboutFeedsBody: "新职位：<a href=\"../jobs.xml\">jobs.xml</a>（另有 <a href=\"../jobs.atom\">jobs.atom</a> 和 <a href=\"../jobs.json\">jobs.json</a>）。新档案：<a href=\"../talents.xml\">talents.xml</a>（另有 <a href=\"../talents.atom\">talents.atom</a> 和 <a href=\"../talents.json\">talents.json</a>）。全部帖子在 <a href=\"../feed.xml\">feed.xml</a>。目录是 <a href=\"../index.json\">index.json</a>。",
      aboutPrivacy: "为什么拒绝电话和个人邮箱？",
      aboutPrivacyBody: "看板是公开的。电话一律不允许。人才帖不能写邮箱。职位最多写一个招聘邮箱，而且域名必须和公司网站一致。",
      aboutDuration: "帖子保留多久？",
      aboutDurationBody: "职位保留 60 天，人才档案保留 180 天，从 <code>posted</code> 或 <code>renewed</code> 起算。公司页一直保留，直到所有者删除。到期的帖子会被移除，页面也不再存在。",
      aboutLanguages: "一篇帖子可以中英都写吗？",
      aboutLanguagesBody: "可以。同一篇帖子可以中英都写。按钮和标题跟随浏览器：偏好中文时用中文，否则用英文。帖子正文保持作者写的语言。只有 <code>languages</code> 恰好是 <code>zh</code> 时，页面才标成中文。没有按语言拆开的网址。",
      aboutIndex: "索引如何工作？",
      aboutIndexBody: "OpenJob 每天读取 Greenhouse、Lever、Ashby 和 Workable 的公开职位源。它只保存标题、公司、地点、部门、类型、日期，以及雇主页面的链接。它不保存职位描述，也不保存任何人的姓名。健康的源里消失的职位会被关闭。失败的源保留 48 小时，然后隐藏。索引职位会标明来源并链出去。它们不是 OpenJob 上的帖子，也不适用 CC BY。",
      aboutClaim: "公司如何认领页面？",
      aboutClaimBody: "添加或编辑 <code>companies/&lt;letter&gt;/&lt;slug&gt;.md</code>，把 <code>owners</code> 设为应控制该公司的 GitHub 登录名。在 <code>https://&lt;company-domain&gt;/.well-known/openjob.txt</code> 发布这些登录名，一行一个。检查器会读取该文件。列出全部所有者时，Pull Request 可以自动合并。否则由维护者审核。认领之后，<code>index: \"off\"</code> 会停止索引该公司的职位板。",
      aboutOptOut: "公司如何退出索引？",
      aboutOptOutBody: "开一个 GitHub issue，或者开一个 Pull Request，把该职位板加到 <code>sources/denylist.yml</code>。维护者会移除它，目标是在 24 小时内完成。认领页面并设置 <code>index: \"off\"</code> 也能让想保留页面的公司退出索引。",
      aboutWho: "谁在维护？",
      aboutWhoBody: "Softprobe 维护 <a href=\"https://github.com/softprobe/openjob\">softprobe/openjob</a>。帖子以 CC BY 4.0 授权，代码以 MIT 授权。可以 fork 这个仓库。",
    },
  };

  function lookup(table, key) {
    var node = table;
    var parts = String(key || "").split(".");
    for (var i = 0; i < parts.length; i += 1) {
      if (node == null || typeof node !== "object") return undefined;
      node = node[parts[i]];
    }
    return node;
  }

  function text(ui, key) {
    var value = lookup(STRINGS[ui] || STRINGS.en, key);
    if (value == null) value = lookup(STRINGS.en, key);
    return value;
  }

  function preferred() {
    var params;
    try {
      params = new URLSearchParams(window.location.search);
    } catch (error) {
      params = { get: function () { return null; } };
    }
    var query = params.get("ui");
    if (query === "zh" || query === "en") return query;
    try {
      var saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === "zh" || saved === "en") return saved;
    } catch (error) {
      /* Storage can be blocked. Fall through to the browser languages. */
    }
    var list = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || ""];
    for (var i = 0; i < list.length; i += 1) {
      var primary = String(list[i] || "").toLowerCase().split("-")[0];
      if (primary === "zh") return "zh";
    }
    return "en";
  }

  function renderValue(value, el) {
    if (typeof value === "function") {
      return value(el.getAttribute("data-count") || "", el.getAttribute("data-pages") || "");
    }
    return value;
  }

  function apply(ui) {
    var lang = ui === "zh" ? "zh" : "en";
    var root = document.documentElement;
    if (!root.dataset.contentLang) root.dataset.contentLang = root.lang || "en";
    root.lang = lang === "zh" ? "zh" : root.dataset.contentLang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var value = text(lang, el.getAttribute("data-i18n"));
      if (value == null) return;
      if (el.getAttribute("data-i18n-html") === "1") {
        if (!el.dataset.i18nEn) el.dataset.i18nEn = el.innerHTML;
        el.innerHTML = lang === "en" ? el.dataset.i18nEn : String(renderValue(value, el));
        return;
      }
      var rendered = renderValue(value, el);
      if (typeof rendered === "string") el.textContent = rendered;
    });
    document.querySelectorAll("[data-i18n-attrs]").forEach(function (el) {
      el.getAttribute("data-i18n-attrs").split(",").forEach(function (pair) {
        var bits = pair.split(":");
        var attr = bits[0];
        var key = bits.slice(1).join(":");
        var value = text(lang, key);
        var rendered = renderValue(value, el);
        if (attr && typeof rendered === "string") el.setAttribute(attr, rendered);
      });
    });
    document.querySelectorAll("[data-lang-toggle]").forEach(function (button) {
      button.textContent = lang === "zh" ? "EN" : "中文";
      button.setAttribute("aria-pressed", lang === "zh" ? "true" : "false");
    });
  }

  function remember(ui) {
    try {
      window.localStorage.setItem(STORAGE_KEY, ui);
    } catch (error) {
      /* The choice still applies for this page view. */
    }
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.has("ui")) {
        params.delete("ui");
        var next = params.toString();
        var hash = window.location.hash || "";
        var path = window.location.pathname;
        window.history.replaceState(null, "", (next ? path + "?" + next : path) + hash);
      }
    } catch (error) {
      /* Leave the address alone when the history API is unavailable. */
    }
  }

  function bind() {
    document.querySelectorAll("[data-lang-toggle]").forEach(function (button) {
      button.addEventListener("click", function () {
        var next = preferred() === "zh" ? "en" : "zh";
        /* After a ?ui= link, preferred() would keep returning that query. */
        remember(next);
        apply(next);
        document.dispatchEvent(new CustomEvent("openjob-ui", { detail: next }));
      });
    });
  }

  window.OpenJobUI = {
    strings: STRINGS,
    preferred: preferred,
    text: function (key) { return text(preferred(), key); },
    apply: apply,
    remember: remember,
  };

  function start() {
    apply(preferred());
    bind();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
}());
