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
      kicker: "GitHub-native classifieds",
      deck: "Jobs and talent profiles, published as pull requests. No accounts. No phone numbers.",
      tabs: { all: "All", job: "Jobs", talent: "Talent", company: "Companies" },
      kind: { job: "Job", talent: "Talent", company: "Company" },
      q: "Role, skill, or keyword",
      location: "Location",
      remote: "Remote",
      language: "Language",
      tag: "Tag",
      examples: "Show samples",
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
      missing: "The index is not here yet. GitHub Pages builds it from the posts. Locally, from the repo root: python -m validator build-index --root . --out site/index.json",
      sample: "Sample",
      federated: "Own repo",
      apply: "Apply",
      applyEmail: "Apply by email",
      howToApply: "How to apply",
      copyEmail: "Copy email",
      copied: "Copied",
      website: "Website",
      profile: "Profile",
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
      aboutWhatBody: "OpenJob is a job board that lives in a Git repository: you post a role or a profile with a pull request, people find it on a static page, and the file expires unless someone renews it.",
      aboutPost: "How do I post a job or a talent profile?",
      aboutApply: "How do I apply?",
      aboutPrivacy: "Why are phone numbers and personal emails rejected?",
      aboutPrivacyBody: "The board is public. Phone numbers are never accepted. Talent posts cannot contain an email. A job may list one hiring address, and only when that domain matches the company website.",
      aboutDuration: "How long does a post stay up?",
      aboutLanguages: "Can a post be in English and Chinese?",
      aboutWho: "Who maintains this?",
    },
    zh: {
      kicker: "用 Pull Request 发布的分类信息",
      deck: "职位和人才档案都通过 Pull Request 发布。没有账号系统，也不收集电话。",
      tabs: { all: "全部", job: "职位", talent: "人才", company: "公司" },
      kind: { job: "职位", talent: "人才", company: "公司" },
      q: "职位、技能或关键词",
      location: "地点",
      remote: "远程",
      language: "语言",
      tag: "标签",
      examples: "显示示例",
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
      missing: "索引还没生成。GitHub Pages 会根据帖子构建。本地在仓库根目录运行：python -m validator build-index --root . --out site/index.json",
      sample: "示例",
      federated: "独立仓库",
      apply: "申请",
      applyEmail: "邮件申请",
      howToApply: "如何申请",
      copyEmail: "复制邮箱",
      copied: "已复制",
      website: "网站",
      profile: "档案",
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
      aboutWhatBody: "OpenJob 是放在 Git 仓库里的招聘板：用 Pull Request 发布职位或人才档案，读者打开一个静态页面，文件到期后会被删除，除非有人续期。",
      aboutPost: "如何发布职位或人才档案？",
      aboutPostBody: "把模板复制到 <code>jobs/</code>、<code>talents/</code> 或 <code>companies/</code>，然后开 Pull Request。只改帖子的请求会在检查通过后自动合并。",
      aboutApply: "如何申请？",
      aboutApplyBody: "申请方式写在职位页上，可以是公司域名上的邮箱、一个 https 链接，或两者都有。人才档案是在 <code>talents/</code> 下新增文件的 Pull Request。不要写电话或个人邮箱。",
      aboutPrivacy: "为什么拒绝电话和个人邮箱？",
      aboutPrivacyBody: "看板是公开的。电话一律不允许。人才帖不能写邮箱。职位最多写一个招聘邮箱，而且域名必须和公司网站一致。",
      aboutDuration: "帖子保留多久？",
      aboutDurationBody: "职位保留 60 天，人才档案保留 180 天，从 <code>posted</code> 或 <code>renewed</code> 起算。公司页一直保留，直到所有者删除。到期的帖子会被移除，页面也不再存在。",
      aboutLanguages: "一篇帖子可以中英都写吗？",
      aboutLanguagesBody: "可以。同一篇帖子可以中英都写。按钮和标题跟随浏览器：偏好中文时用中文，否则用英文。帖子正文保持作者写的语言。只有 <code>languages</code> 恰好是 <code>zh</code> 时，页面才标成中文。没有按语言拆开的网址。",
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
