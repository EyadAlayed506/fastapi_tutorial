/* Hisbah demo client — vanilla JS, no build step. */
"use strict";

const I18N = {
  en: {
    appName: "Hisbah", tagline: "Your private AI finance assistant",
    lockFoot: "Your financial data is encrypted on this device. The PIN never leaves it.",
    createPin: "Create a 4-digit PIN", confirmPin: "Confirm your PIN", enterPin: "Enter your PIN",
    pinMismatch: "PINs didn't match — try again", locked: "Vault locked",
    tabHome: "Home", tabTxns: "Activity", tabChat: "Assistant", tabPrivacy: "Privacy",
    titleHome: "Overview", titleTxns: "Transactions", titleChat: "Ask Hisbah", titlePrivacy: "Privacy & Settings",
    emptyTitle: "Let's bring in your transactions",
    emptyBody: "Connect a bank through the SAMA Open Banking sandbox, or paste a bank SMS. Everything is parsed, categorised and stored encrypted on this device.",
    connectBank: "Connect a bank", addSms: "Paste a bank SMS",
    spentThisMonth: "Spent this month", vsSameDays: "vs same days last month",
    income: "Income", available: "Available", projected: "Projected", lastMonthSaved: "Saved last month",
    accounts: "Accounts", pace: "Spending pace", thisMonth: "This month", lastMonth: "Last month", day: "Day",
    insights: "Insights", budgets: "Budgets", edit: "Edit", categories: "Where your money went",
    showTable: "Table", showBars: "Bars", upcoming: "Recurring & subscriptions", next: "next",
    perMonth: "/mo", onTrack: "On track", atRisk: "At risk", over: "Over budget",
    of: "of", projectedShort: "proj.", search: "Search merchant or description", all: "All", add: "Add",
    noTxns: "No transactions match.", source: "Source", account: "Account", date: "Date", category: "Category",
    applyMerchant: "Apply to all transactions from this merchant (Hisbah will remember)", save: "Save",
    rawText: "Raw text", whyCategory: "Why this category", parserRules: "Parser rules fired", confidence: "Parse confidence",
    updated: "Updated", txnsWord: "transactions",
    addTitle: "Add transactions", sms: "Bank SMS", statement: "Statement (CSV)",
    smsHelp: "Paste an Arabic or English bank SMS. The bilingual rule-based parser extracts the fields — nothing is sent anywhere.",
    sampleAr: "Arabic sample", sampleEn: "English sample", sampleSalary: "Salary SMS",
    parse: "Parse", saveVault: "Save to encrypted vault", saved: "Saved to vault", duplicate: "Already in your vault",
    amount: "Amount", direction: "Direction", merchant: "Merchant", channel: "Channel", card: "Card", balance: "Balance",
    debit: "Debit", credit: "Credit",
    stmtHelp: "Upload a CSV statement (Date, Description, Amount — Arabic or English headers). It is parsed locally.",
    useSample: "Use sample statement", imported: "Imported", newWord: "new",
    chatWelcome: "Hi! I'm Hisbah. I answer from your encrypted on-device data — every number comes from the finance engine, not from guesswork. Ask in English or Arabic.",
    ask: "Ask about your money…", how: "How I got this answer", intent: "Intent", entities: "Understood",
    engineCalls: "Engine calls", generatedBy: "Phrased by", facts: "Verified facts",
    tplEngine: "on-device template (no LLM)", localLlm: "local LLM (number-checked)",
    privacyHero: "Your data stays on this device",
    pv1: "Every transaction is encrypted with AES-256-GCM before it touches the disk",
    pv2: "The data key is wrapped by a key derived from your PIN (scrypt)",
    pv3: "Auto-locks after 10 minutes of inactivity",
    pv4: "Financial data sent to cloud AI services:",
    banks: "Connected banks", connected: "Connected", notConnected: "Not connected", connect: "Connect", disconnect: "Disconnect",
    syncNow: "Sync now", synced: "Synced", onDisk: "What's actually on disk", records: "encrypted records",
    sampleRow: "A real row from the local database:", aiPipeline: "How the AI works",
    computation: "Numbers", language: "Language", network: "Network activity", noNetwork: "No network calls yet.",
    netNote: "Only Open Banking sandbox calls — they fetch data to the device; nothing financial is uploaded.",
    budgetsEdit: "Monthly budgets (SAR)", budgetsSaved: "Budgets saved", lockNow: "Lock now", reset: "Reset demo (wipe vault)",
    resetConfirm: "This deletes all encrypted data and the PIN. Continue?",
    chooseBank: "Choose your bank", sandboxNote: "Simulated SAMA Open Banking sandbox — fictional banks, synthetic data.",
    consentTitle: "Hisbah requests read-only access",
    permAccounts: "Account details", permAccountsD: "Account type, nickname and masked number",
    permBalances: "Balances", permBalancesD: "Current balances of your accounts",
    permTxns: "Transactions", permTxnsD: "Up to 6 months of transaction history",
    consentNote1: "Read-only — Hisbah can never move money.", consentNote2: "Valid for 90 days. Revoke anytime from Privacy.",
    consentNote3: "Data is downloaded to this device and encrypted. It is not stored on Hisbah servers.",
    continueBank: "Continue to", cancel: "Cancel", back: "Back",
    bankAuth: "Authorise third-party access", bankReq: "Hisbah is requesting access to these accounts:",
    approve: "Approve", decline: "Decline", declined: "You declined the request. No data was shared.",
    syncing: "Fetching and categorising transactions…", done: "Done",
    resultTitle: "Bank connected", fetched: "Transactions fetched", newRecords: "New records stored", autoCat: "Auto-categorised",
    accountsN: "Accounts",
    errGeneric: "Something went wrong",
  },
  ar: {
    appName: "حِسبة", tagline: "مساعدك المالي الذكي والخاص",
    lockFoot: "بياناتك المالية مشفّرة على هذا الجهاز، ورمزك السري لا يغادره أبداً.",
    createPin: "أنشئ رمزاً سرياً من 4 أرقام", confirmPin: "أكّد الرمز السري", enterPin: "أدخل الرمز السري",
    pinMismatch: "الرمزان غير متطابقين — حاول مجدداً", locked: "تم قفل الخزنة",
    tabHome: "الرئيسية", tabTxns: "العمليات", tabChat: "المساعد", tabPrivacy: "الخصوصية",
    titleHome: "نظرة عامة", titleTxns: "العمليات", titleChat: "اسأل حِسبة", titlePrivacy: "الخصوصية والإعدادات",
    emptyTitle: "لنبدأ بإضافة عملياتك",
    emptyBody: "اربط حسابك البنكي عبر بيئة الخدمات المصرفية المفتوحة التجريبية (ساما)، أو الصق رسالة بنكية. كل شيء يُحلَّل ويُصنَّف ويُخزَّن مشفّراً على جهازك.",
    connectBank: "اربط حساباً بنكياً", addSms: "الصق رسالة بنكية",
    spentThisMonth: "مصروفات هذا الشهر", vsSameDays: "مقارنة بنفس الفترة من الشهر الماضي",
    income: "الدخل", available: "المتاح", projected: "المتوقع", lastMonthSaved: "ادخار الشهر الماضي",
    accounts: "الحسابات", pace: "وتيرة الصرف", thisMonth: "هذا الشهر", lastMonth: "الشهر الماضي", day: "اليوم",
    insights: "رؤى ونصائح", budgets: "الميزانيات", edit: "تعديل", categories: "أين ذهبت أموالك",
    showTable: "جدول", showBars: "أعمدة", upcoming: "الالتزامات والاشتراكات", next: "القادم",
    perMonth: "/شهرياً", onTrack: "ضمن الحد", atRisk: "معرّضة للتجاوز", over: "تجاوزت الحد",
    of: "من", projectedShort: "متوقع", search: "ابحث باسم المتجر أو الوصف", all: "الكل", add: "إضافة",
    noTxns: "لا توجد عمليات مطابقة.", source: "المصدر", account: "الحساب", date: "التاريخ", category: "الفئة",
    applyMerchant: "طبّق على كل عمليات هذا المتجر (سيتذكر حِسبة اختيارك)", save: "حفظ",
    rawText: "النص الأصلي", whyCategory: "سبب التصنيف", parserRules: "القواعد المطبّقة", confidence: "دقة التحليل",
    updated: "تم تحديث", txnsWord: "عملية",
    addTitle: "إضافة عمليات", sms: "رسالة بنكية", statement: "كشف حساب (CSV)",
    smsHelp: "الصق رسالة بنكية بالعربية أو الإنجليزية. المحلل ثنائي اللغة يستخرج البيانات محلياً — لا يُرسل شيء لأي جهة.",
    sampleAr: "مثال عربي", sampleEn: "مثال إنجليزي", sampleSalary: "رسالة راتب",
    parse: "تحليل", saveVault: "حفظ في الخزنة المشفّرة", saved: "تم الحفظ في الخزنة", duplicate: "موجودة مسبقاً في خزنتك",
    amount: "المبلغ", direction: "النوع", merchant: "المتجر", channel: "القناة", card: "البطاقة", balance: "الرصيد",
    debit: "خصم", credit: "إيداع",
    stmtHelp: "ارفع كشف حساب CSV (التاريخ، الوصف، المبلغ — بعناوين عربية أو إنجليزية). يُحلَّل محلياً.",
    useSample: "استخدم كشفاً تجريبياً", imported: "تم استيراد", newWord: "جديدة",
    chatWelcome: "أهلاً! أنا حِسبة. أجيبك من بياناتك المشفّرة على جهازك — كل رقم يأتي من المحرك المالي وليس تخميناً. اسألني بالعربية أو الإنجليزية.",
    ask: "اسأل عن مصروفاتك…", how: "كيف وصلت لهذه الإجابة", intent: "النية", entities: "ما فهمته",
    engineCalls: "استدعاءات المحرك", generatedBy: "الصياغة", facts: "الحقائق المتحقق منها",
    tplEngine: "قوالب على الجهاز (بدون نموذج لغوي)", localLlm: "نموذج لغوي محلي (مع تحقق من الأرقام)",
    privacyHero: "بياناتك تبقى على جهازك",
    pv1: "كل عملية تُشفَّر بـ AES-256-GCM قبل حفظها على القرص",
    pv2: "مفتاح البيانات محمي بمفتاح مشتق من رمزك السري (scrypt)",
    pv3: "قفل تلقائي بعد 10 دقائق من عدم الاستخدام",
    pv4: "البيانات المالية المرسلة لخدمات ذكاء اصطناعي سحابية:",
    banks: "البنوك المرتبطة", connected: "مرتبط", notConnected: "غير مرتبط", connect: "ربط", disconnect: "فك الربط",
    syncNow: "مزامنة الآن", synced: "تمت المزامنة", onDisk: "ما المحفوظ فعلياً على القرص", records: "سجلات مشفّرة",
    sampleRow: "سجل حقيقي من قاعدة البيانات المحلية:", aiPipeline: "كيف يعمل الذكاء الاصطناعي",
    computation: "الأرقام", language: "اللغة", network: "نشاط الشبكة", noNetwork: "لا توجد اتصالات بعد.",
    netNote: "فقط اتصالات بيئة الخدمات المصرفية المفتوحة — تجلب البيانات إلى الجهاز ولا يُرفع أي شيء مالي.",
    budgetsEdit: "الميزانيات الشهرية (ريال)", budgetsSaved: "تم حفظ الميزانيات", lockNow: "اقفل الآن", reset: "إعادة ضبط العرض (مسح الخزنة)",
    resetConfirm: "سيتم حذف كل البيانات المشفّرة والرمز السري. متابعة؟",
    chooseBank: "اختر بنكك", sandboxNote: "بيئة تجريبية تحاكي الخدمات المصرفية المفتوحة من ساما — بنوك وهمية وبيانات اصطناعية.",
    consentTitle: "حِسبة يطلب صلاحية قراءة فقط",
    permAccounts: "بيانات الحسابات", permAccountsD: "نوع الحساب واسمه ورقمه المخفي",
    permBalances: "الأرصدة", permBalancesD: "الأرصدة الحالية لحساباتك",
    permTxns: "العمليات", permTxnsD: "سجل العمليات لآخر 6 أشهر",
    consentNote1: "قراءة فقط — لا يستطيع حِسبة تحويل أي أموال.", consentNote2: "صالحة 90 يوماً، ويمكنك إلغاؤها متى شئت من صفحة الخصوصية.",
    consentNote3: "تُنزَّل البيانات إلى جهازك وتُشفَّر، ولا تُخزَّن على خوادم حِسبة.",
    continueBank: "المتابعة إلى", cancel: "إلغاء", back: "رجوع",
    bankAuth: "تفويض وصول طرف ثالث", bankReq: "يطلب حِسبة الوصول إلى الحسابات التالية:",
    approve: "موافقة", decline: "رفض", declined: "رفضت الطلب. لم تتم مشاركة أي بيانات.",
    syncing: "جارٍ جلب العمليات وتصنيفها…", done: "تم",
    resultTitle: "تم ربط البنك", fetched: "العمليات المستلمة", newRecords: "سجلات جديدة محفوظة", autoCat: "صُنّفت تلقائياً",
    accountsN: "الحسابات",
    errGeneric: "حدث خطأ ما",
  },
};

const SAMPLES = {
  ar: "شراء عبر نقاط البيع\nبطاقة: ٤٥٢٣ مدى-أبل باي\nمبلغ: ٨٧٫٥٠ ر.س\nلدى: هنقرستيشن\nفي: ٢٦-١٠-١٢ ٢١:١٤\nالرصيد: ٣٬٢١٠٫٤٠ ر.س",
  en: "PoS Purchase of SAR 64.00 at STARBUCKS on 12/10/2026 using card ending 4523. Available balance SAR 3,146.40",
  salary: "إيداع راتب\nمبلغ: 14,500.00 ريال\nإلى حساب: **4523\nفي: 2026-09-27",
};

const S = {
  token: null, lang: "en", tab: "home", cats: {}, dash: null, txns: null, budgets: null,
  txnCat: null, txnQ: "", chat: [], chatSuggestions: null, catView: "bars",
  pin: "", pinMode: "unlock", firstPin: "",
};
try { S.lang = localStorage.getItem("hisbah.lang") || ((navigator.language || "").startsWith("ar") ? "ar" : "en"); } catch { /* storage unavailable */ }

const $ = (sel, root = document) => root.querySelector(sel);
const t = (k) => (I18N[S.lang] && I18N[S.lang][k]) || I18N.en[k] || k;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (x, dp = 2) => Number(x || 0).toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp });
const money = (x, dp = 2) => (S.lang === "ar" ? `${num(x, dp)} ر.س` : `SAR ${num(x, dp)}`);
const catLabel = (c) => (S.cats[c] ? S.cats[c][S.lang] : c);
const catIcon = (c) => (S.cats[c] ? S.cats[c].icon : "📦");
const locale = () => (S.lang === "ar" ? "ar-u-nu-latn-ca-gregory" : "en-GB");
const fmtDate = (iso, opts = { day: "numeric", month: "short" }) => new Intl.DateTimeFormat(locale(), opts).format(new Date(iso));
const kfmt = (v) => (v >= 1000 ? `${num(v / 1000, v >= 10000 ? 0 : 1)}k` : num(v, 0));

/* ------------------------------------------------------------------ API */
async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (S.token) headers.Authorization = `Bearer ${S.token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { method, headers, body: form || (body !== undefined ? JSON.stringify(body) : undefined) });
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (res.status === 401 && S.token && !path.startsWith("/api/auth/")) {
    S.token = null;
    showLock(t("locked"));
    throw new Error(t("locked"));
  }
  if (!res.ok) throw new Error((data && (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))) || t("errGeneric"));
  return data;
}

function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.hidden = true), 2600);
}

/* ------------------------------------------------------------------ i18n */
function applyLang() {
  document.documentElement.lang = S.lang;
  document.documentElement.dir = S.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  document.querySelectorAll(".lang-btn").forEach((b) => (b.textContent = S.lang === "ar" ? "English" : "عربي"));
  try { localStorage.setItem("hisbah.lang", S.lang); } catch { /* ignore */ }
}

/* ------------------------------------------------------------------ Lock screen */
async function boot() {
  applyLang();
  const st = await api("/api/auth/status");
  S.pinMode = st.initialized ? "unlock" : "setup1";
  showLock();
}

function showLock(msg = "") {
  closeSheet();
  $("#app").hidden = true;
  $("#lock").hidden = false;
  S.pin = "";
  if (S.pinMode !== "setup1" && S.pinMode !== "setup2") S.pinMode = "unlock";
  renderLock(msg);
}

function renderLock(msg = "") {
  $("#lock-title").textContent = t({ setup1: "createPin", setup2: "confirmPin", unlock: "enterPin" }[S.pinMode]);
  $("#pin-dots").innerHTML = [0, 1, 2, 3].map((i) => `<i class="${i < S.pin.length ? "on" : ""}"></i>`).join("");
  $("#lock-msg").textContent = msg;
  $("#keypad").innerHTML = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"]
    .map((k) => (k === "" ? "<span></span>" : `<button data-key="${k}" class="${k === "⌫" ? "ghost" : ""}" aria-label="${k === "⌫" ? "Delete" : k}">${k}</button>`))
    .join("");
}

async function pressKey(k) {
  if (k === "⌫") S.pin = S.pin.slice(0, -1);
  else if (S.pin.length < 4) S.pin += k;
  renderLock();
  if (S.pin.length < 4) return;
  const pin = S.pin;
  try {
    if (S.pinMode === "setup1") {
      S.firstPin = pin; S.pinMode = "setup2"; S.pin = ""; renderLock();
      return;
    }
    if (S.pinMode === "setup2") {
      if (pin !== S.firstPin) { S.pinMode = "setup1"; S.pin = ""; shake(); renderLock(t("pinMismatch")); return; }
      S.token = (await api("/api/auth/setup", { method: "POST", body: { pin } })).token;
    } else {
      S.token = (await api("/api/auth/unlock", { method: "POST", body: { pin } })).token;
    }
    S.pinMode = "unlock";
    enterApp();
  } catch (e) {
    S.pin = ""; shake(); renderLock(e.message);
  }
}

function shake() {
  const el = $("#pin-dots");
  el.classList.remove("shake"); void el.offsetWidth; el.classList.add("shake");
}

async function enterApp() {
  $("#lock").hidden = true;
  $("#app").hidden = false;
  if (!Object.keys(S.cats).length) S.cats = await api("/api/categories");
  S.dash = S.txns = null;
  go(S.tab);
}

/* ------------------------------------------------------------------ Navigation */
const TITLES = { home: "titleHome", txns: "titleTxns", chat: "titleChat", privacy: "titlePrivacy" };

function go(tab) {
  S.tab = tab;
  document.querySelectorAll("#tabbar button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  $("#screen-title").textContent = t(TITLES[tab]);
  $("#screen").scrollTop = 0;
  ({ home: renderHome, txns: renderTxns, chat: renderChat, privacy: renderPrivacy })[tab]();
}

function invalidate() { S.dash = null; S.txns = null; }

/* ------------------------------------------------------------------ Home */
async function renderHome() {
  const el = $("#screen");
  if (!S.dash) {
    el.innerHTML = `<div class="spinner"></div>`;
    try { S.dash = await api("/api/dashboard"); } catch (e) { el.innerHTML = `<p class="muted">${esc(e.message)}</p>`; return; }
  }
  if (S.tab !== "home") return;
  const d = S.dash;
  $("#today-label").textContent = fmtDate(d.today, { weekday: "long", day: "numeric", month: "long" });
  if (!d.has_data) {
    el.innerHTML = `<div class="card empty"><div class="big">🏦</div><h2>${t("emptyTitle")}</h2><p>${t("emptyBody")}</p>
      <div class="stack"><button class="btn block" data-action="connect">${t("connectBank")}</button>
      <button class="btn block secondary" data-action="add">${t("addSms")}</button></div></div>`;
    return;
  }
  const cmp = d.vs_last_month;
  const up = cmp.delta > 0;
  const pct = cmp.pct != null ? `${Math.abs(cmp.pct).toFixed(0)}%` : "—";
  const lm = d.last_month;
  el.innerHTML = `
    <div class="card hero">
      <div class="muted tiny">${t("spentThisMonth")}</div>
      <div class="hero-num">${money(d.this_month.spending)}</div>
      <span class="pill" data-tip="${esc(`${t("thisMonth")}: ${money(cmp.total_a)}<br>${t("lastMonth")}: ${money(cmp.total_b)}`)}">${up ? "▲" : "▼"} ${pct} ${t("vsSameDays")}</span>
      <div class="hero-row">
        <div><span class="muted tiny">${t("available")}</span><b>${money(d.accounts.filter((a) => a.type !== "CreditCard").reduce((s, a) => s + a.balance, 0), 0)}</b></div>
        <div><span class="muted tiny">${t("projected")}</span><b>${money(d.forecast.projected_total, 0)}</b></div>
        <div><span class="muted tiny">${t("lastMonthSaved")}</span><b>${lm.savings_rate != null ? `${lm.savings_rate.toFixed(0)}%` : "—"}</b></div>
      </div>
    </div>
    ${d.insights.length ? `<div class="card"><h3>${t("insights")}</h3>${d.insights.slice(0, 5).map(insightHtml).join("")}</div>` : ""}
    <div class="card"><h3>${t("pace")} <small>${t("day")} ${d.forecast.days_elapsed}/${d.forecast.days_in_month}</small></h3>
      <div class="legend"><span><i></i>${t("thisMonth")}</span><span><i class="dash"></i>${t("lastMonth")}</span></div>
      <div class="chart" id="pace-chart" dir="ltr"></div></div>
    <div class="card"><h3>${t("budgets")} <button class="btn small secondary" data-action="edit-budgets">${t("edit")}</button></h3>
      ${d.budgets.items.map(budgetHtml).join("")}</div>
    <div class="card"><h3>${t("categories")} <button class="btn small secondary" data-action="toggle-catview">${S.catView === "bars" ? t("showTable") : t("showBars")}</button></h3>
      <div id="cat-view">${categoryView(d.breakdown)}</div></div>
    ${recurringHtml(d.recurring)}
    ${accountsHtml(d.accounts)}`;
  drawPace($("#pace-chart"), d.daily);
}

function insightHtml(i) {
  const icon = { budget: "🎯", anomaly: "⚠️", trend: "📈", subscriptions: "🔁", savings: "💰" }[i.kind] || "💡";
  return `<div class="insight ${i.severity}"><div class="ico">${icon}</div><div>${esc(i[S.lang])}</div></div>`;
}

function budgetHtml(b) {
  const st = { on_track: ["✓", t("onTrack")], at_risk: ["!", t("atRisk")], over: ["✕", t("over")] }[b.status];
  const width = Math.min(100, b.pct);
  const projMark = b.status === "at_risk" ? Math.min(100, (100 * b.projected) / b.limit) : null;
  return `<div class="budget" data-tip="${esc(`${catLabel(b.category)}<br>${money(b.spent)} ${t("of")} ${money(b.limit)}<br>${t("projectedShort")}: ${money(b.projected)}`)}">
    <div class="row between"><span>${catIcon(b.category)} ${esc(catLabel(b.category))}</span>
      <span class="num">${money(b.spent, 0)} <span class="muted">${t("of")} ${money(b.limit, 0)}</span></span></div>
    <div class="meter"><i class="${b.status}" style="width:${width}%"></i>${projMark ? `<em style="inset-inline-start:calc(${projMark}% - 1px)" title="${t("projectedShort")}"></em>` : ""}</div>
    <div class="row between" style="margin:6px 0 0"><span class="status ${b.status}">${st[0]} ${st[1]}</span>
      <span class="tiny muted">${b.status === "at_risk" ? `${t("projectedShort")} ${money(b.projected, 0)}` : `${b.pct.toFixed(0)}%`}</span></div></div>`;
}

function categoryView(bd) {
  const cats = bd.categories;
  if (S.catView === "table") {
    return `<table class="data"><thead><tr><th>${t("category")}</th><th class="n">SAR</th><th class="n">%</th><th class="n">#</th></tr></thead><tbody>
      ${cats.map((c) => `<tr><td>${catIcon(c.category)} ${esc(catLabel(c.category))}</td><td class="n">${num(c.total)}</td><td class="n">${c.share.toFixed(1)}</td><td class="n">${c.count}</td></tr>`).join("")}
      </tbody></table>`;
  }
  const max = Math.max(...cats.map((c) => c.total), 1);
  return `<div class="bars">${cats.map((c) => `
    <div class="bar-row" data-tip="${esc(`${catLabel(c.category)}<br>${money(c.total)} · ${c.share.toFixed(1)}%<br>${c.count} ${t("txnsWord")}`)}" data-cat="${c.category}">
      <span>${catIcon(c.category)}</span>
      <div><div class="meta"><span>${esc(catLabel(c.category))}</span><span class="tiny">${c.share.toFixed(0)}%</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${(100 * c.total) / max}%"></div></div></div>
      <span class="val num">${money(c.total, 0)}</span></div>`).join("")}</div>`;
}

function recurringHtml(r) {
  if (!r.items.length) return "";
  return `<div class="card"><h3>${t("upcoming")} <small>${money(r.monthly_total, 0)}${t("perMonth")}</small></h3>
    ${r.items.map((i) => `<div class="list-item" style="cursor:default"><div class="avatar">${catIcon(i.category)}</div>
      <div><div class="name">${esc(i.merchant)}</div><div class="sub">${t("next")} ${fmtDate(i.next_date)}</div></div>
      <div class="amt num">${money(i.average_amount)}</div></div>`).join("")}</div>`;
}

function accountsHtml(accs) {
  if (!accs.length) return "";
  return `<div class="card"><h3>${t("accounts")}</h3>${accs.map((a) => `
    <div class="list-item" style="cursor:default"><div class="avatar">${a.type === "CreditCard" ? "💳" : "🏦"}</div>
    <div><div class="name">${esc(S.lang === "ar" ? a.nickname_ar : a.nickname)} <span class="muted">${esc(a.masked)}</span></div>
    <div class="sub">${esc(a.bank)} · sandbox</div></div>
    <div class="amt num ${a.balance >= 0 ? "" : ""}">${money(a.balance)}</div></div>`).join("")}</div>`;
}

/* Two-series cumulative line chart with crosshair + tooltip */
function drawPace(host, daily) {
  if (!host) return;
  const a = daily.this_month, b = daily.last_month;
  const W = 340, H = 170, L = 38, R = 58, T = 10, B = 22;
  const n = Math.max(b.length, a.length, 2);
  const maxY = Math.max(...a, ...b, 1);
  const step = Math.pow(10, Math.floor(Math.log10(maxY))) / 2;
  const top = Math.ceil(maxY / step) * step;
  const x = (i) => L + (i / (n - 1)) * (W - L - R);
  const y = (v) => T + (1 - v / top) * (H - T - B);
  const path = (arr) => arr.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * top);
  const xt = [1, 8, 15, 22, n].filter((d, i, arr) => d <= n && arr.indexOf(d) === i);
  const la = a.length - 1, lb = b.length - 1;
  let ya = y(a[la]), yb = y(b[lb]);
  if (Math.abs(ya - yb) < 14 && x(la) > x(lb) - 40) { if (ya < yb) ya -= 7; else yb -= 7; }
  host.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t("pace"))}">
    ${ticks.map((v) => `<line class="${v ? "gridline" : "baseline"}" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>
      <text class="tick" x="${L - 6}" y="${y(v) + 3}" text-anchor="end">${kfmt(v)}</text>`).join("")}
    ${xt.map((d) => `<text class="tick" x="${x(d - 1)}" y="${H - 6}" text-anchor="middle">${d}</text>`).join("")}
    <path class="s2" d="${path(b)}" fill="none" stroke-width="2" stroke-linejoin="round"/>
    <path class="s1" d="${path(a)}" fill="none" stroke-width="2" stroke-linejoin="round"/>
    <circle class="dot1" cx="${x(la)}" cy="${y(a[la])}" r="4.5"/>
    <text class="dlabel" x="${x(la) + 8}" y="${ya + 4}">${kfmt(a[la])}</text>
    <text class="dlabel" x="${x(lb) + 6}" y="${yb + 4}">${kfmt(b[lb])}</text>
    <g id="xh" visibility="hidden"><line class="crosshair" y1="${T}" y2="${H - B}"/>
      <circle class="dot2" r="4.5"/><circle class="dot1" r="4.5"/></g>
    <rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="transparent" id="hit"/></svg>`;
  const svg = host.querySelector("svg"), g = host.querySelector("#xh"), tip = $("#tooltip");
  const move = (ev) => {
    const pt = svg.createSVGPoint();
    const src = ev.touches ? ev.touches[0] : ev;
    pt.x = src.clientX; pt.y = src.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    const i = Math.max(0, Math.min(n - 1, Math.round(((p.x - L) / (W - L - R)) * (n - 1))));
    const [line, d2, d1] = g.children;
    line.setAttribute("x1", x(i)); line.setAttribute("x2", x(i));
    d1.setAttribute("cx", x(i)); d1.setAttribute("cy", y(a[Math.min(i, la)]));
    d1.setAttribute("visibility", i <= la ? "visible" : "hidden");
    d2.setAttribute("cx", x(i)); d2.setAttribute("cy", y(b[Math.min(i, lb)]));
    g.setAttribute("visibility", "visible");
    showTip(src, `<b>${t("day")} ${i + 1}</b><br>${t("thisMonth")}: ${i <= la ? money(a[i], 0) : "—"}<br>${t("lastMonth")}: ${money(b[Math.min(i, lb)], 0)}`);
  };
  const leave = () => { g.setAttribute("visibility", "hidden"); tip.hidden = true; };
  const hit = host.querySelector("#hit");
  hit.addEventListener("pointermove", move);
  hit.addEventListener("pointerleave", leave);
  hit.addEventListener("touchmove", move, { passive: true });
  hit.addEventListener("touchend", leave);
}

function showTip(src, html) {
  const tip = $("#tooltip"), dev = $(".device").getBoundingClientRect();
  tip.innerHTML = html;
  tip.hidden = false;
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let left = src.clientX - dev.left + 12, top = src.clientY - dev.top - h - 12;
  if (left + w > dev.width - 8) left = src.clientX - dev.left - w - 12;
  if (top < 8) top = src.clientY - dev.top + 16;
  tip.style.left = `${Math.max(8, left)}px`;
  tip.style.top = `${top}px`;
}

/* ------------------------------------------------------------------ Transactions */
async function renderTxns() {
  const el = $("#screen");
  if (!S.txns) {
    el.innerHTML = `<div class="spinner"></div>`;
    try { S.txns = (await api("/api/transactions?limit=1000")).items; } catch (e) { el.innerHTML = `<p class="muted">${esc(e.message)}</p>`; return; }
  }
  if (S.tab !== "txns") return;
  const present = [...new Set(S.txns.map((x) => x.category))];
  el.innerHTML = `
    <div class="row"><input class="search" id="txn-q" type="search" placeholder="${t("search")}" value="${esc(S.txnQ)}">
      <button class="btn" data-action="add" style="flex:none">＋ ${t("add")}</button></div>
    <div class="chips"><button class="chip ${!S.txnCat ? "active" : ""}" data-cat-filter="">${t("all")}</button>
      ${Object.keys(S.cats).filter((c) => present.includes(c)).map((c) => `<button class="chip ${S.txnCat === c ? "active" : ""}" data-cat-filter="${c}">${catIcon(c)} ${esc(catLabel(c))}</button>`).join("")}</div>
    <div id="txn-list"></div>`;
  renderTxnList();
  $("#txn-q").addEventListener("input", (e) => { S.txnQ = e.target.value; renderTxnList(); });
}

function renderTxnList() {
  const q = S.txnQ.trim().toLowerCase();
  const items = S.txns.filter((x) => (!S.txnCat || x.category === S.txnCat) &&
    (!q || x.merchant.toLowerCase().includes(q) || x.description.toLowerCase().includes(q)));
  if (!items.length) { $("#txn-list").innerHTML = `<p class="muted empty">${S.txns.length ? t("noTxns") : t("emptyBody")}</p>`; return; }
  let html = "", day = "";
  for (const x of items.slice(0, 400)) {
    const d = x.date.slice(0, 10);
    if (d !== day) { day = d; html += `<div class="day-head">${fmtDate(d, { weekday: "short", day: "numeric", month: "short", year: "numeric" })}</div>`; }
    const src = { open_banking: "🏦", sms: "✉️", statement: "📄" }[x.source] || "";
    html += `<button class="list-item" data-txn="${x.id}"><div class="avatar">${catIcon(x.category)}</div>
      <div style="min-width:0"><div class="name">${esc(x.merchant)}</div><div class="sub">${src} ${esc(catLabel(x.category))} · ${esc(x.account || "")}</div></div>
      <div class="amt num ${x.direction}">${x.direction === "credit" ? "+" : "−"}${money(x.amount)}</div></button>`;
  }
  $("#txn-list").innerHTML = html;
}

function openTxn(id) {
  const x = S.txns.find((r) => r.id === id);
  if (!x) return;
  const srcLabel = { open_banking: "Open Banking (sandbox)", sms: "SMS", statement: "CSV statement" }[x.source] || x.source;
  openSheet(`<div class="grabber"></div>
    <div class="row" style="margin-bottom:12px"><div class="avatar" style="width:52px;height:52px;font-size:24px">${catIcon(x.category)}</div>
      <div><h2 style="margin:0">${esc(x.merchant)}</h2><div class="amt num ${x.direction}" style="font-size:20px">${x.direction === "credit" ? "+" : "−"}${money(x.amount)}</div></div></div>
    <dl class="kv"><dt>${t("date")}</dt><dd>${fmtDate(x.date, { dateStyle: "medium", timeStyle: "short" })}</dd>
      <dt>${t("account")}</dt><dd>${esc(x.account || "—")}</dd><dt>${t("source")}</dt><dd><span class="badge">${esc(srcLabel)}</span></dd>
      <dt>${t("whyCategory")}</dt><dd><code>${esc(x.category_reason || "—")}</code></dd>
      ${x.confidence != null && x.source === "sms" ? `<dt>${t("confidence")}</dt><dd><div class="confidence"><i style="width:${x.confidence * 100}%"></i></div></dd>` : ""}</dl>
    ${x.parser_rules ? `<p class="tiny muted">${t("parserRules")}</p><div class="rules">${x.parser_rules.map((r) => `<span class="badge">${esc(r)}</span>`).join("")}</div>` : ""}
    <p class="tiny muted">${t("rawText")}</p><div class="raw" dir="auto">${esc(x.description)}</div>
    <div class="field" style="margin-top:14px"><label for="recat">${t("category")}</label>
      <select id="recat">${Object.keys(S.cats).map((c) => `<option value="${c}" ${c === x.category ? "selected" : ""}>${catIcon(c)} ${esc(catLabel(c))}</option>`).join("")}</select></div>
    <label class="row tiny" style="margin-bottom:14px;color:var(--ink-2)"><input type="checkbox" id="recat-all" checked> ${t("applyMerchant")}</label>
    <button class="btn block" id="recat-save">${t("save")}</button>`);
  $("#recat-save").onclick = async () => {
    try {
      const r = await api(`/api/transactions/${x.id}`, { method: "PATCH", body: { category: $("#recat").value, apply_to_merchant: $("#recat-all").checked } });
      toast(`${t("updated")} ${r.updated} ${t("txnsWord")}`);
      closeSheet(); invalidate(); go(S.tab);
    } catch (e) { toast(e.message); }
  };
}

/* Add sheet: SMS / statement */
function openAdd(mode = "sms") {
  openSheet(`<div class="grabber"></div><h2>${t("addTitle")}</h2>
    <div class="seg"><button class="${mode === "sms" ? "active" : ""}" data-add-mode="sms">✉️ ${t("sms")}</button>
      <button class="${mode === "csv" ? "active" : ""}" data-add-mode="csv">📄 ${t("statement")}</button></div>
    ${mode === "sms" ? `
      <p class="tiny muted">${t("smsHelp")}</p>
      <div class="chips" style="padding-top:0"><button class="chip" data-sample="ar">${t("sampleAr")}</button>
        <button class="chip" data-sample="en">${t("sampleEn")}</button><button class="chip" data-sample="salary">${t("sampleSalary")}</button></div>
      <div class="field"><textarea id="sms-text" dir="auto" placeholder="…"></textarea></div>
      <button class="btn block secondary" id="sms-parse">🔍 ${t("parse")}</button>
      <div id="sms-result"></div>` : `
      <p class="tiny muted">${t("stmtHelp")}</p>
      <div class="field"><input type="file" id="csv-file" accept=".csv,text/csv"></div>
      <div class="stack"><button class="btn block" id="csv-upload">⬆️ ${t("statement")}</button>
        <button class="btn block secondary" id="csv-sample">${t("useSample")}</button></div>`}`);
  if (mode === "sms") {
    $("#sms-parse").onclick = parseSms;
  } else {
    $("#csv-upload").onclick = () => { const f = $("#csv-file").files[0]; if (f) uploadCsv(f); };
    $("#csv-sample").onclick = async () => uploadCsv(await (await fetch("/static/sample_statement.csv")).blob(), "sample_statement.csv");
  }
}

async function parseSms() {
  const text = $("#sms-text").value.trim();
  if (!text) return;
  try {
    const p = await api("/api/parse", { method: "POST", body: { text } });
    const dir = p.direction ? t(p.direction) : "—";
    $("#sms-result").innerHTML = `<div class="card" style="margin-top:14px;box-shadow:none">
      <dl class="kv"><dt>${t("amount")}</dt><dd>${p.amount != null ? money(p.amount) : "—"}</dd>
        <dt>${t("direction")}</dt><dd>${dir}</dd><dt>${t("merchant")}</dt><dd>${esc(p.merchant || "—")}</dd>
        <dt>${t("date")}</dt><dd>${p.occurred_at ? fmtDate(p.occurred_at, { dateStyle: "medium", timeStyle: "short" }) : "—"}</dd>
        <dt>${t("channel")}</dt><dd>${esc(p.channel || "—")}</dd><dt>${t("card")}</dt><dd>${p.card_last4 ? "•••• " + esc(p.card_last4) : "—"}</dd>
        <dt>${t("balance")}</dt><dd>${p.balance != null ? money(p.balance) : "—"}</dd>
        <dt>${t("category")}</dt><dd>${catIcon(p.category)} ${esc(catLabel(p.category))} <code class="tiny muted">${esc(p.category_reason)}</code></dd>
        <dt>${t("confidence")}</dt><dd><div class="confidence"><i style="width:${p.confidence * 100}%"></i></div></dd></dl>
      <p class="tiny muted">${t("parserRules")}</p><div class="rules">${p.rules.map((r) => `<span class="badge">${esc(r)}</span>`).join("")}</div>
      <button class="btn block" id="sms-save" style="margin-top:14px" ${p.amount == null ? "disabled" : ""}>🔐 ${t("saveVault")}</button></div>`;
    $("#sms-save").onclick = async () => {
      try {
        const r = await api("/api/ingest/sms", { method: "POST", body: { text } });
        toast(r.saved ? t("saved") : t("duplicate"));
        if (r.saved) { closeSheet(); invalidate(); go(S.tab); }
      } catch (e) { toast(e.message); }
    };
  } catch (e) { toast(e.message); }
}

async function uploadCsv(blob, name = "statement.csv") {
  const form = new FormData();
  form.append("file", blob, blob.name || name);
  try {
    const r = await api("/api/ingest/statement", { method: "POST", form });
    toast(`${t("imported")} ${r.rows} · ${r.new} ${t("newWord")}`);
    closeSheet(); invalidate(); go(S.tab);
  } catch (e) { toast(e.message); }
}

/* ------------------------------------------------------------------ Assistant */
function renderChat() {
  const el = $("#screen");
  const sugg = S.chatSuggestions || (S.lang === "ar"
    ? ["كم صرفت على المطاعم هذا الشهر؟", "كيف وضع ميزانيتي؟", "وش اشتراكاتي؟", "هل فيه عمليات غريبة؟", "قارن هذا الشهر بالشهر الماضي"]
    : ["How much did I spend on dining this month?", "Am I on track with my budgets?", "What are my subscriptions?", "Any unusual transactions?", "Compare this month to last month"]);
  el.innerHTML = `<div class="chat"><div class="msgs" id="msgs">
      <div class="bubble bot">${esc(t("chatWelcome"))}</div>
      ${S.chat.map(msgHtml).join("")}</div>
    <div class="composer"><div class="chips">${sugg.map((s) => `<button class="chip" data-ask="${esc(s)}">${esc(s)}</button>`).join("")}</div>
      <form id="ask-form"><input id="ask-input" autocomplete="off" placeholder="${t("ask")}" dir="auto"><button class="btn" aria-label="Send"><span>➤</span></button></form></div></div>`;
  $("#ask-form").onsubmit = (e) => { e.preventDefault(); const v = $("#ask-input").value.trim(); if (v) ask(v); };
  el.scrollTop = el.scrollHeight;
}

function msgHtml(m) {
  if (m.role === "me") return `<div class="bubble me" dir="auto">${esc(m.text)}</div>`;
  if (m.role === "typing") return `<div class="typing">…</div>`;
  const r = m.result;
  const u = r.understanding;
  const ent = [u.category && `category=${u.category}`, u.merchant && `merchant=${u.merchant}`, u.periods.length && `period=${u.periods.join(" → ")}`, `lang=${u.language}`].filter(Boolean).join(", ");
  return `<div class="bubble bot" dir="auto">${esc(r.answer)}
    <details><summary>${t("how")}</summary><div class="trace">
      <div>${t("intent")}: <code>${esc(u.intent)}</code></div>
      <div>${t("entities")}: <code>${esc(ent)}</code></div>
      <div>${t("engineCalls")}: ${r.engine_calls.map((c) => `<code>${esc(c)}</code>`).join(" ") || "—"}</div>
      <div>${t("generatedBy")}: ${r.generated_by === "local_llm" ? t("localLlm") : t("tplEngine")}</div>
      <div>${t("facts")}:</div><div class="facts">${esc(JSON.stringify(r.facts, null, 2).slice(0, 3000))}</div>
    </div></details></div>`;
}

async function ask(q) {
  S.chat.push({ role: "me", text: q }, { role: "typing" });
  renderChat();
  try {
    const r = await api("/api/assistant", { method: "POST", body: { question: q } });
    S.chat = S.chat.filter((m) => m.role !== "typing");
    S.chat.push({ role: "bot", result: r });
    S.chatSuggestions = r.suggestions;
  } catch (e) {
    S.chat = S.chat.filter((m) => m.role !== "typing");
    toast(e.message);
  }
  if (S.tab === "chat") renderChat();
}

/* ------------------------------------------------------------------ Privacy & settings */
async function renderPrivacy() {
  const el = $("#screen");
  el.innerHTML = `<div class="spinner"></div>`;
  let p, banks, budgets;
  try { [p, banks, budgets] = await Promise.all([api("/api/privacy"), api("/api/banks"), api("/api/budgets")]); }
  catch (e) { el.innerHTML = `<p class="muted">${esc(e.message)}</p>`; return; }
  if (S.tab !== "privacy") return;
  const s = p.storage;
  const anyConnected = banks.some((b) => b.connected);
  el.innerHTML = `
    <div class="card hero"><h3 style="color:#fff">🛡️ ${t("privacyHero")}</h3>
      <ul class="check-list"><li><span>✓</span>${t("pv1")}</li><li><span>✓</span>${t("pv2")}</li><li><span>✓</span>${t("pv3")}</li>
      <li><span>✓</span><span>${t("pv4")} <b style="font-size:18px">${p.financial_data_sent_to_cloud_ai}</b></span></li></ul></div>
    <div class="card"><h3>${t("banks")} ${anyConnected ? `<button class="btn small" data-action="sync">↻ ${t("syncNow")}</button>` : ""}</h3>
      ${banks.map((b) => `<div class="list-item" style="cursor:default"><div class="bank-logo" style="background:${b.color}">${esc(b.name[0])}</div>
        <div><div class="name">${esc(S.lang === "ar" ? b.name_ar : b.name)}</div><div class="sub">${b.connected ? "🟢 " + t("connected") : "⚪ " + t("notConnected")}</div></div>
        ${b.connected ? `<button class="btn small danger" data-disconnect="${b.id}">${t("disconnect")}</button>` : `<button class="btn small" data-action="connect" data-bank="${b.id}">${t("connect")}</button>`}</div>`).join("")}</div>
    <div class="card"><h3>${t("onDisk")} <small>${esc(s.db_file)} · ${num(s.db_size_bytes / 1024, 0)} KB</small></h3>
      <p class="tiny" style="margin-top:0"><b>${s.encrypted_records}</b> ${t("records")}</p>
      ${s.sample_row_on_disk ? `<p class="tiny muted">${t("sampleRow")}</p><div class="hex">id: ${esc(s.sample_row_on_disk.id)}<br>source: ${esc(s.sample_row_on_disk.source)}<br>fingerprint: ${esc(s.sample_row_on_disk.fingerprint)}<br>ciphertext (${s.sample_row_on_disk.ciphertext_bytes} B): ${esc(s.sample_row_on_disk.ciphertext_hex)}</div>` : ""}
      <dl class="kv" style="margin-top:12px">${Object.entries(p.crypto).map(([k, v]) => `<dt>${esc(k.replaceAll("_", " "))}</dt><dd>${esc(v)}</dd>`).join("")}</dl></div>
    <div class="card"><h3>${t("aiPipeline")}</h3><dl class="kv">
      <dt>${t("computation")}</dt><dd>${esc(p.ai.computation)}</dd><dt>${t("language")}</dt><dd>${esc(p.ai.language)}</dd>
      ${p.ai.llm_endpoint ? `<dt>LLM</dt><dd>${esc(p.ai.llm_endpoint)}</dd>` : ""}</dl></div>
    <div class="card"><h3>${t("network")}</h3><p class="tiny muted" style="margin-top:0">${t("netNote")}</p>
      ${p.network_log.length ? `<table class="data"><tbody>${p.network_log.slice(-8).reverse().map((c) => `<tr><td class="tiny">${esc(c.at.slice(11))}</td><td><code class="tiny">${esc(c.endpoint)}</code></td><td class="tiny">${esc(c.bank)}</td></tr>`).join("")}</tbody></table>` : `<p class="muted tiny">${t("noNetwork")}</p>`}</div>
    <div class="card" id="budgets-card"><h3>${t("budgetsEdit")}</h3><form id="budget-form"><div class="budget-grid">
      ${["groceries", "dining", "shopping", "transport", "fuel", "entertainment", "health", "subscriptions", "bills"].map((c) => `
        <label for="b-${c}">${catIcon(c)} ${esc(catLabel(c))}</label><input id="b-${c}" name="${c}" type="number" min="0" step="50" inputmode="numeric" value="${budgets[c] ?? ""}" placeholder="—">`).join("")}
      </div><button class="btn block" style="margin-top:14px">${t("save")}</button></form></div>
    <div class="stack" style="margin-bottom:10px"><button class="btn block secondary" data-action="lock">🔒 ${t("lockNow")}</button>
      <button class="btn block danger" data-action="reset">${t("reset")}</button></div>`;
  $("#budget-form").onsubmit = async (e) => {
    e.preventDefault();
    const body = {};
    new FormData(e.target).forEach((v, k) => { if (v !== "" && Number(v) > 0) body[k] = Number(v); });
    try { await api("/api/budgets", { method: "PUT", body }); toast(t("budgetsSaved")); S.dash = null; } catch (err) { toast(err.message); }
  };
}

/* ------------------------------------------------------------------ Bank connection flow */
async function connectFlow(bankId) {
  let banks;
  try { banks = await api("/api/banks"); } catch (e) { toast(e.message); return; }
  const flow = { bank: banks.find((b) => b.id === bankId) || null, consent: null };
  const head = (title, backFn) => `<div class="flow-head">${backFn ? `<button class="icon-btn" id="flow-back" aria-label="${t("back")}">${S.lang === "ar" ? "→" : "←"}</button>` : ""}<b>${title}</b>
    <button class="icon-btn" id="flow-close" style="margin-inline-start:auto" aria-label="${t("cancel")}">✕</button></div>`;
  const wire = (backFn) => { $("#flow-close").onclick = closeSheet; if (backFn) $("#flow-back").onclick = backFn; };

  const choose = () => {
    openSheet(`${head(t("chooseBank"))}<div class="flow-body"><p class="tiny muted" style="margin-top:0">${t("sandboxNote")}</p>
      ${banks.map((b) => `<button class="bank-card" data-pick="${b.id}"><div class="bank-logo" style="background:${b.color}">${esc(b.name[0])}</div>
        <div><b>${esc(S.lang === "ar" ? b.name_ar : b.name)}</b><div class="tiny muted">${b.connected ? t("connected") : "SAMA Open Banking · sandbox"}</div></div></button>`).join("")}</div>`, true);
    wire();
    document.querySelectorAll("[data-pick]").forEach((btn) => (btn.onclick = () => { flow.bank = banks.find((b) => b.id === btn.dataset.pick); consent(); }));
  };

  const consent = async () => {
    try { flow.consent = await api("/api/bank/consent", { method: "POST", body: { bank_id: flow.bank.id } }); } catch (e) { toast(e.message); return; }
    const perms = [["🏦", "permAccounts"], ["💰", "permBalances"], ["🧾", "permTxns"]];
    openSheet(`${head(t("consentTitle"), choose)}<div class="flow-body">
      <div class="row" style="margin-bottom:14px"><div class="logo" style="width:48px;height:48px;font-size:26px;margin:0;background:var(--brand)">ح</div>
        <span style="font-size:22px">⇄</span><div class="bank-logo" style="background:${flow.bank.color};width:48px;height:48px">${esc(flow.bank.name[0])}</div></div>
      ${perms.map(([i, k]) => `<div class="perm"><span>${i}</span><div>${t(k)}<small>${t(k + "D")}</small></div></div>`).join("")}
      <ul class="check-list" style="margin-top:16px"><li><span>🔒</span>${t("consentNote1")}</li><li><span>⏱️</span>${t("consentNote2")}</li><li><span>📱</span>${t("consentNote3")}</li></ul>
      <p class="tiny muted">consent_id: <code>${esc(flow.consent.consent_id)}</code> · ${esc(flow.consent.status)}</p></div>
      <div class="flow-foot"><button class="btn block" id="to-bank">${t("continueBank")} ${esc(S.lang === "ar" ? flow.bank.name_ar : flow.bank.name)}</button>
        <button class="btn block secondary" id="flow-cancel">${t("cancel")}</button></div>`, true);
    wire(choose);
    $("#flow-cancel").onclick = closeSheet;
    $("#to-bank").onclick = bankPage;
  };

  const bankPage = () => {
    openSheet(`<div class="bank-page"><div class="bank-bar" style="background:${flow.bank.color}">
        <div class="row between"><b style="font-size:18px">${esc(S.lang === "ar" ? flow.bank.name_ar : flow.bank.name)}</b><button class="icon-btn" id="flow-close" style="background:rgba(255,255,255,.2);color:#fff">✕</button></div>
        <div class="tiny" style="opacity:.85;margin-top:6px">${t("bankAuth")}</div></div>
      <div class="sandbox-ribbon">⚠️ SANDBOX · ${t("sandboxNote")}</div>
      <div class="flow-body"><p>${t("bankReq")}</p>
        <label class="perm"><input type="checkbox" checked disabled><div>${S.lang === "ar" ? "الحساب الجاري" : "Current Account"}<small>•••• ${flow.bank.id === "nakheel" ? "4523" : "7710"}</small></div></label>
        <label class="perm"><input type="checkbox" checked disabled><div>${S.lang === "ar" ? "بطاقة فيزا" : "Visa Signature"}<small>•••• 8812</small></div></label>
        <p class="tiny muted">${t("permAccounts")} · ${t("permBalances")} · ${t("permTxns")}</p></div>
      <div class="flow-foot"><button class="btn block" style="background:${flow.bank.color}" id="approve">${t("approve")}</button>
        <button class="btn block secondary" id="decline">${t("decline")}</button></div></div>`, true);
    $("#flow-close").onclick = closeSheet;
    $("#approve").onclick = () => authorise(true);
    $("#decline").onclick = () => authorise(false);
  };

  const authorise = async (approve) => {
    let r;
    try { r = await api("/api/bank/authorise", { method: "POST", body: { consent_id: flow.consent.consent_id, approve } }); } catch (e) { toast(e.message); return; }
    if (r.status !== "Authorised") {
      openSheet(`${head(t("bankAuth"))}<div class="flow-body empty"><div class="big">🚫</div><p>${t("declined")}</p></div>
        <div class="flow-foot"><button class="btn block secondary" id="flow-done">${t("done")}</button></div>`, true);
      wire(); $("#flow-done").onclick = closeSheet;
      return;
    }
    openSheet(`<div class="flow-body"><div class="spinner"></div><p style="text-align:center">${t("syncing")}</p></div>`, true);
    try {
      const s = await api("/api/bank/sync", { method: "POST" });
      openSheet(`${head(t("resultTitle"))}<div class="flow-body"><div class="big-check">✅</div>
        <dl class="kv" style="margin-top:20px;font-size:15px"><dt>${t("accountsN")}</dt><dd>${s.accounts}</dd>
          <dt>${t("fetched")}</dt><dd>${s.fetched}</dd><dt>${t("newRecords")}</dt><dd>${s.new} 🔐</dd>
          <dt>${t("autoCat")}</dt><dd>${s.categorized_pct}%</dd></dl></div>
        <div class="flow-foot"><button class="btn block" id="flow-done">${t("done")}</button></div>`, true);
      wire();
      $("#flow-done").onclick = () => { closeSheet(); invalidate(); go("home"); };
    } catch (e) { closeSheet(); toast(e.message); }
  };

  if (flow.bank) consent(); else choose();
}

/* ------------------------------------------------------------------ Sheet helpers */
function openSheet(html, full = false) {
  const sh = $("#sheet");
  sh.className = `sheet${full ? " full" : ""}`;
  sh.innerHTML = html;
  sh.hidden = false;
  $("#sheet-backdrop").hidden = false;
}
function closeSheet() { $("#sheet").hidden = true; $("#sheet-backdrop").hidden = true; $("#sheet").innerHTML = ""; }

/* ------------------------------------------------------------------ Global events */
document.addEventListener("click", async (e) => {
  const el = e.target.closest("button, [data-txn]");
  if (!el) { if (e.target.id === "sheet-backdrop") closeSheet(); return; }
  const d = el.dataset;
  if (d.key !== undefined) return pressKey(d.key);
  if (d.tab) return go(d.tab);
  if (d.txn) return openTxn(d.txn);
  if (d.catFilter !== undefined) { S.txnCat = d.catFilter || null; return renderTxns(); }
  if (d.sample) { $("#sms-text").value = SAMPLES[d.sample]; return parseSms(); }
  if (d.addMode) return openAdd(d.addMode);
  if (d.ask) return ask(d.ask);
  if (d.disconnect) { try { await api(`/api/bank/${d.disconnect}`, { method: "DELETE" }); renderPrivacy(); } catch (err) { toast(err.message); } return; }
  switch (d.action) {
    case "toggle-lang":
      S.lang = S.lang === "ar" ? "en" : "ar";
      applyLang(); S.chatSuggestions = null;
      if (!$("#lock").hidden) renderLock(); else go(S.tab);
      break;
    case "lock":
      try { await api("/api/auth/lock", { method: "POST" }); } catch { /* already locked */ }
      S.token = null; S.chat = []; invalidate(); showLock();
      break;
    case "connect": connectFlow(d.bank); break;
    case "add": openAdd("sms"); break;
    case "edit-budgets": go("privacy"); setTimeout(() => $("#budgets-card")?.scrollIntoView({ behavior: "smooth" }), 400); break;
    case "toggle-catview": S.catView = S.catView === "bars" ? "table" : "bars"; $("#cat-view").innerHTML = categoryView(S.dash.breakdown); el.textContent = S.catView === "bars" ? t("showTable") : t("showBars"); break;
    case "sync":
      try { const s = await api("/api/bank/sync", { method: "POST" }); toast(`${t("synced")} · ${s.new} ${t("newWord")}`); invalidate(); renderPrivacy(); } catch (err) { toast(err.message); }
      break;
    case "reset":
      if (!confirm(t("resetConfirm"))) return;
      try { await api("/api/reset", { method: "POST" }); } catch { /* ignore */ }
      S.token = null; S.chat = []; invalidate(); S.pinMode = "setup1"; S.tab = "home"; showLock();
      break;
  }
});
$("#sheet-backdrop").addEventListener("click", closeSheet);

// Hover tooltips for any element carrying data-tip (bars, budgets, deltas).
document.addEventListener("pointermove", (e) => {
  const el = e.target.closest("[data-tip]");
  if (el) showTip(e, el.dataset.tip);
  else if (!e.target.closest("#pace-chart")) $("#tooltip").hidden = true;
});

document.addEventListener("keydown", (e) => {
  if ($("#lock").hidden) { if (e.key === "Escape") closeSheet(); return; }
  if (/^\d$/.test(e.key)) pressKey(e.key);
  else if (e.key === "Backspace") pressKey("⌫");
});

boot().catch((e) => { document.body.innerHTML = `<p style="padding:20px">${esc(e.message)}</p>`; });
