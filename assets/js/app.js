// assets/js/app.js — hard‑mapped PDF pages
const grid = document.getElementById('grid');
const q = document.getElementById('q');

// Путь к PDF
const PDF_PATH = 'assets/pdf/races.pdf';

// Жёсткая привязка страниц (нумерация как в просмотрщике PDF, с 1)
const PAGE_MAP = {
  "Гномы": 3,
  "Люди": 4,
  "Дроу": 5,
  "Зверолюды": 6,
  "Демоны": 7,
  "Эльфы": 8,
  "Хоббиты": 9,
  "Лотары": 10,
  "Орки": 11,
  "Циклопы": 12,
  "Огры": 13,
  "Нордиры": 14,
  "Ринка": 15,
  "Саури": 16,
  "Тролли": 17
};

let races = [];

function pageFor(name, index) {
  return PAGE_MAP[name] ?? null;
}

function cardTpl(it, i) {
  const page = pageFor(it.name, i);
  const href = page ? `${PDF_PATH}#page=${page}` : PDF_PATH;
  const badge = page ? `<span class="badge">стр. ${page}</span>` : `<span class="badge badge--wip">PDF</span>`;
  const quote = it.quote ? `<p class="quote">«${it.quote}»</p>` : '';
  return `
    <a class="card" href="${href}" target="_blank" rel="noopener">
      ${badge}
      <h3>${it.name || 'Без названия'}</h3>
      ${it.description ? `<p class="note">${it.description}</p>` : ''}
      ${quote}
    </a>
  `;
}

function render(list) {
  if (!grid) return;
  if (!list.length) { grid.innerHTML = `<p class="note">Ничего не найдено.</p>`; return; }
  grid.innerHTML = list.map((it, i) => cardTpl(it, i)).join('');
}

// Загрузка данных
fetch('data/races.json')
  .then(r => r.json())
  .then(data => { races = Array.isArray(data) ? data : []; render(races); })
  .catch(() => render([]));

// Поиск
q?.addEventListener('input', e => {
  const s = e.target.value.toLowerCase().trim();
  const filtered = races.filter(it => {
    const inName = (it.name || '').toLowerCase().includes(s);
    const inDesc = (it.description || '').toLowerCase().includes(s);
    const inTraits = (it.traits || []).some(t => (`${t.title} ${t.text}`).toLowerCase().includes(s));
    return inName || inDesc || inTraits;
  });
  render(filtered);
});
