import "dotenv/config";
import fs from "fs";
import path from "path";
import OpenAI from "openai";
import { Telegraf } from "telegraf";

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN);
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const MODEL = process.env.OPENAI_MODEL || "gpt-4.1-mini";
const ROUTER_MODEL = process.env.ROUTER_MODEL || MODEL;
const PROMPT_DIR = process.env.PROMPT_DIR || "./prompts";
const MAX_NPC_TURNS = Number(process.env.MAX_NPC_TURNS || 24);

// ---------- Utilities ----------
function listTxtFilesRecursive(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listTxtFilesRecursive(full));
    else if (entry.isFile() && entry.name.toLowerCase().endsWith(".txt")) out.push(full);
  }
  return out;
}

function readFileUtf8(p) {
  return fs.readFileSync(p, "utf8");
}

function ensurePromptDir() {
  if (!fs.existsSync(PROMPT_DIR)) {
    throw new Error(`PROMPT_DIR не найден: ${PROMPT_DIR}. Создай папку prompts/ и распакуй туда .txt`);
  }
}

function pickPrompt(files, regexList, label) {
  const rx = regexList.map((r) => (r instanceof RegExp ? r : new RegExp(r, "i")));
  const found = files.find((f) => rx.some((r) => r.test(path.basename(f))));
  if (!found) {
    const names = files.map((f) => path.basename(f)).sort().join("\n");
    throw new Error(
      `Не найден промпт для "${label}". Ищу по: ${rx.map(String).join(", ")}\n\nДоступные .txt:\n${names}`
    );
  }
  return found;
}

function chunk(text, size = 3900) {
  const parts = [];
  let s = String(text || "");
  while (s.length > size) {
    parts.push(s.slice(0, size));
    s = s.slice(size);
  }
  parts.push(s);
  return parts.filter(Boolean);
}

// ---------- NPC IDs ----------
const NPC = {
  ROUTER: "ROUTER",
  NARRATOR: "NARRATOR",
  PARTNER: "PARTNER",

  ARTEM: "ARTEM",
  ILYA: "ILYA",
  SVETLANA: "SVETLANA",
  TATYANA: "TATYANA",
  ALINA: "ALINA",
  FATHER: "FATHER",

  BARMAN: "BARMAN",
  RESTAURANT_MANAGER: "RESTAURANT_MANAGER",
  RESTAURANT_CHEF: "RESTAURANT_CHEF",
  RESTAURANT_ADMIN: "RESTAURANT_ADMIN",
};

const ALIASES = {
  [NPC.PARTNER]: ["напарник", "партнер", "partner"],
  [NPC.NARRATOR]: ["нарратор", "повествователь", "narrator"],

  [NPC.ARTEM]: ["артём", "артем", "логинов", "artem", "loginov"],
  [NPC.ILYA]: ["илья", "крот", "ilya", "krot"],
  [NPC.SVETLANA]: ["светлана", "svetlana"],
  [NPC.TATYANA]: ["татьяна", "tatyana"],
  [NPC.ALINA]: ["алина", "alina"],
  [NPC.FATHER]: ["отец", "сергей", "лебедев", "father"],

  [NPC.BARMAN]: ["бармен", "barman"],
  [NPC.RESTAURANT_MANAGER]: ["менеджер", "управляющий", "manager"],
  [NPC.RESTAURANT_CHEF]: ["повар", "шеф", "chef"],
  [NPC.RESTAURANT_ADMIN]: ["админ", "администратор", "admin"],
};

function findNpcByText(text) {
  const t = (text || "").toLowerCase();
  for (const [id, names] of Object.entries(ALIASES)) {
    if (names.some((n) => t.includes(n))) return id;
  }
  return null;
}

// ---------- Prompt loading (auto-discovery) ----------
let PROMPT_PATHS = null;

function loadPromptPaths() {
  ensurePromptDir();
  const files = listTxtFilesRecursive(PROMPT_DIR);

  // Роутер / нарратор / напарник
  const router = pickPrompt(files, [/router/i, /global.*router/i, /00.*router/i], "ROUTER");
  const narrator = pickPrompt(files, [/narrator/i, /case.*narrator/i, /00a.*narrator/i], "NARRATOR");
  const partner = pickPrompt(files, [/partner/i, /напарник/i, /07.*partner/i], "PARTNER");

  // NPC (базовые)
  const artem = pickPrompt(files, [/artem/i, /логинов/i], "ARTEM");
  const father = pickPrompt(files, [/father/i, /отец/i, /лебедев/i], "FATHER");
  const svetlana = pickPrompt(files, [/svetlana/i, /светлана/i], "SVETLANA");

  const barman = pickPrompt(files, [/barman/i, /бармен/i], "BARMAN");
  const restManager = pickPrompt(files, [/restaurant.*manager/i, /manager/i, /управляющий/i], "RESTAURANT_MANAGER");
  const restChef = pickPrompt(files, [/restaurant.*chef/i, /chef/i, /повар/i, /шеф/i], "RESTAURANT_CHEF");
  const restAdmin = pickPrompt(files, [/restaurant.*admin/i, /admin/i, /администратор/i], "RESTAURANT_ADMIN");

  // staged
  const ilya0 = pickPrompt(files, [/ilya.*stage.*0/i, /ilya.*free/i, /stage_0/i], "ILYA_STAGE_0");
  const ilya1 = pickPrompt(files, [/ilya.*stage.*1/i, /ilya.*detain/i, /stage_1/i], "ILYA_STAGE_1");
  const ilya2 = pickPrompt(files, [/ilya.*stage.*2/i, /ilya.*coop/i, /stage_2/i], "ILYA_STAGE_2");

  const tat0 = pickPrompt(files, [/tatyana.*stage.*0/i, /tatyana.*0/i, /tatyana.*system/i], "TATYANA_STAGE_0");
  // stage 1 может называться по-разному, ищем “after”/“break”
  const tat1 = pickPrompt(files, [/tatyana.*stage.*1/i, /tatyana.*after/i, /tatyana.*break/i], "TATYANA_STAGE_1");

  const ali0 = pickPrompt(files, [/alina.*stage.*0/i, /alina.*0/i, /alina.*system/i], "ALINA_STAGE_0");
  const ali1 = pickPrompt(files, [/alina.*stage.*1/i, /alina.*after/i, /alina.*reveal/i], "ALINA_STAGE_1");

  PROMPT_PATHS = {
    ROUTER: router,
    NARRATOR: narrator,
    PARTNER: partner,
    ARTEM: artem,
    FATHER: father,
    SVETLANA: svetlana,
    BARMAN: barman,
    RESTAURANT_MANAGER: restManager,
    RESTAURANT_CHEF: restChef,
    RESTAURANT_ADMIN: restAdmin,
    ILYA: { 0: ilya0, 1: ilya1, 2: ilya2 },
    TATYANA: { 0: tat0, 1: tat1 },
    ALINA: { 0: ali0, 1: ali1 },
  };
}

function getSystemPrompt(npcId, stage = 0) {
  if (!PROMPT_PATHS) loadPromptPaths();

  if (npcId === NPC.ILYA) return readFileUtf8(PROMPT_PATHS.ILYA[stage] || PROMPT_PATHS.ILYA[0]);
  if (npcId === NPC.TATYANA) return readFileUtf8(PROMPT_PATHS.TATYANA[stage] || PROMPT_PATHS.TATYANA[0]);
  if (npcId === NPC.ALINA) return readFileUtf8(PROMPT_PATHS.ALINA[stage] || PROMPT_PATHS.ALINA[0]);

  const key = npcId;
  const p = PROMPT_PATHS[key];
  if (!p) throw new Error(`Нет промпта для npcId=${npcId}`);
  return readFileUtf8(p);
}

// ---------- In-memory state ----------
const stateByUser = new Map();    // user_id -> state
const memoryByUser = new Map();   // user_id -> { [npcStageKey]: messages[] }

const ALL_OPEN = Object.values(NPC).filter((x) => x !== NPC.ROUTER);

function getState(userId) {
  if (!stateByUser.has(userId)) {
    stateByUser.set(userId, {
      mode: "DIALOGUE",
      open_characters: ALL_OPEN,
      open_evidence: [],
      open_locations: [],
      last_active_character: NPC.PARTNER,
      recent_messages: [],
      npc_stage: {
        [NPC.ILYA]: 0,
        [NPC.TATYANA]: 0,
        [NPC.ALINA]: 0,
      },
    });
  }
  return stateByUser.get(userId);
}

function getNpcMemory(userId, npcStageKey) {
  if (!memoryByUser.has(userId)) memoryByUser.set(userId, {});
  const bag = memoryByUser.get(userId);
  if (!bag[npcStageKey]) bag[npcStageKey] = [];
  return bag[npcStageKey];
}

function pushRecent(state, who, text) {
  state.recent_messages.push({ who, text: String(text).slice(0, 400) });
  if (state.recent_messages.length > 12) state.recent_messages = state.recent_messages.slice(-12);
}

// ---------- OpenAI call ----------
async function callChat({ model, system, messages, temperature = 0.7, max_tokens = 700 }) {
  const resp = await openai.chat.completions.create({
    model,
    messages: [{ role: "system", content: system }, ...messages],
    temperature,
    max_tokens,
  });
  return resp.choices?.[0]?.message?.content?.trim() || "";
}

// ---------- Router ----------
function resolveNpcAndStage(routeTo, state) {
  if (routeTo === NPC.ILYA) return { npcId: NPC.ILYA, stage: state.npc_stage[NPC.ILYA] ?? 0 };
  if (routeTo === NPC.TATYANA) return { npcId: NPC.TATYANA, stage: state.npc_stage[NPC.TATYANA] ?? 0 };
  if (routeTo === NPC.ALINA) return { npcId: NPC.ALINA, stage: state.npc_stage[NPC.ALINA] ?? 0 };
  return { npcId: routeTo, stage: 0 };
}

async function routeMessage(state, userMessage) {
  const m = userMessage.trim();

  // 1) Prefix switch: "артём: ..."
  const prefixMatch = m.match(/^([a-zа-яё0-9 _-]+)\s*:\s*(.+)$/i);
  if (prefixMatch) {
    const maybe = prefixMatch[1].toLowerCase();
    const npc = findNpcByText(maybe);
    if (npc && state.open_characters.includes(npc)) {
      return { route_to: npc, confidence: 0.95, tags: ["prefix_switch"] };
    }
  }

  // 2) Keep focus unless user explicitly calls another NPC by name
  const explicit = findNpcByText(userMessage);
  if (!explicit && state.mode === "DIALOGUE" && state.last_active_character) {
    return { route_to: state.last_active_character, confidence: 0.75, tags: ["keep_focus"] };
  }
  if (explicit && state.open_characters.includes(explicit)) {
    return { route_to: explicit, confidence: 0.8, tags: ["explicit_name"] };
  }

  // 3) LLM Router
  const routerSystem = getSystemPrompt(NPC.ROUTER, 0);
  const payload = {
    case_state: {
      mode: state.mode,
      open_characters: state.open_characters,
      open_locations: state.open_locations,
      open_evidence: state.open_evidence,
      last_active_character: state.last_active_character,
      recent_messages: state.recent_messages,
    },
    user_message: userMessage,
  };

  const out = await callChat({
    model: ROUTER_MODEL,
    system: routerSystem,
    messages: [{ role: "user", content: JSON.stringify(payload) }],
    temperature: 0.1,
    max_tokens: 220,
  });

  try {
    const parsed = JSON.parse(out);
    const r = parsed.route_to;
    if (r && state.open_characters.includes(r)) return parsed;
  } catch (_) {}

  return { route_to: NPC.PARTNER, confidence: 0.2, tags: ["router_fallback"] };
}

// ---------- Commands ----------
bot.start(async (ctx) => {
  const userId = String(ctx.from.id);
  getState(userId);
  await ctx.reply(
`Тестовый бот допросов (NPC).

Команды:
  /list
  /npc <имя|id>
  /stage <ilya|tatyana|alina> <0|1|2>
  /reset
  /state

Можно писать свободным текстом. По умолчанию router выбирает отвечающего.`
  );
});

bot.command("list", async (ctx) => {
  const list = ALL_OPEN.join("\n");
  await ctx.reply(`Доступные NPC:\n${list}\n\nПример: /npc ARTEM или /npc Логинов`);
});

bot.command("npc", async (ctx) => {
  const userId = String(ctx.from.id);
  const state = getState(userId);

  const arg = (ctx.message.text || "").split(" ").slice(1).join(" ").trim();
  if (!arg) return ctx.reply("Формат: /npc ARTEM или /npc Логинов");

  const directId = ALL_OPEN.find((id) => id.toLowerCase() === arg.toLowerCase());
  const byName = findNpcByText(arg);
  const pick = directId || byName;

  if (!pick || !state.open_characters.includes(pick)) {
    return ctx.reply("Не понял, кого выбрать. Используй /list.");
  }

  state.last_active_character = pick;
  state.mode = "DIALOGUE";
  await ctx.reply(`Ок. Активный собеседник: ${pick}`);
});

bot.command("stage", async (ctx) => {
  const userId = String(ctx.from.id);
  const state = getState(userId);

  const parts = (ctx.message.text || "").split(" ").slice(1);
  const who = (parts[0] || "").toLowerCase();
  const stage = Number(parts[1]);

  const map = { ilya: NPC.ILYA, tatyana: NPC.TATYANA, alina: NPC.ALINA };
  const npcId = map[who];

  if (!npcId || Number.isNaN(stage)) {
    return ctx.reply("Формат: /stage ilya 0|1|2  (или tatyana 0|1, alina 0|1)");
  }

  state.npc_stage[npcId] = stage;
  await ctx.reply(`Стадия ${npcId} = ${stage}`);
});

bot.command("reset", async (ctx) => {
  const userId = String(ctx.from.id);
  stateByUser.delete(userId);
  memoryByUser.delete(userId);
  await ctx.reply("Сбросил состояние и память для этого user_id.");
});

bot.command("state", async (ctx) => {
  const userId = String(ctx.from.id);
  const state = getState(userId);
  await ctx.reply("STATE:\n" + JSON.stringify(state, null, 2).slice(0, 3800));
});

// ---------- Main text handler ----------
bot.on("text", async (ctx) => {
  const userId = String(ctx.from.id);
  const state = getState(userId);
  const userText = ctx.message.text;

  try { await ctx.sendChatAction("typing"); } catch {}

  pushRecent(state, "user", userText);

  let route;
  try {
    route = await routeMessage(state, userText);
  } catch (e) {
    console.error("Router error:", e);
    route = { route_to: NPC.PARTNER, confidence: 0.1, tags: ["router_error"] };
  }

  const { npcId, stage } = resolveNpcAndStage(route.route_to, state);

  let systemPrompt;
  try {
    systemPrompt = getSystemPrompt(npcId, stage);
  } catch (e) {
    console.error("Prompt load error:", e);
    await ctx.reply("Ошибка: не смог загрузить промпт. Проверь папку prompts/ и имена .txt");
    return;
  }

  const memKey = `${npcId}:${stage}`;
  const npcMem = getNpcMemory(userId, memKey);
  const messages = [...npcMem, { role: "user", content: userText }];

  let answer = "";
  try {
    answer = await callChat({
      model: MODEL,
      system: systemPrompt,
      messages,
      temperature: 0.7,
      max_tokens: 800,
    });
  } catch (e) {
    console.error("OpenAI error:", e);
    answer = "Ошибка AI-запроса. Проверь OPENAI_API_KEY и модель.";
  }

  // save memory
  npcMem.push({ role: "user", content: userText });
  npcMem.push({ role: "assistant", content: answer });
  if (npcMem.length > MAX_NPC_TURNS) {
    npcMem.splice(0, npcMem.length - MAX_NPC_TURNS);
  }

  state.last_active_character = npcId;
  state.mode = "DIALOGUE";
  pushRecent(state, npcId, answer);

  for (const part of chunk(answer)) {
    await ctx.reply(part);
  }
});

bot.launch();
console.log("Bot started (long polling).");

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
