/**
 * MoneyLog 공통 JavaScript
 */

// ── 숫자 포맷 유틸 ───────────────────────────────────────────────────────────

/**
 * 숫자를 한국 통화 형식으로 포맷
 * @param {number} amount
 * @returns {string} 예: "12,500원"
 */
function formatAmount(amount) {
  return Number(amount).toLocaleString('ko-KR') + '원';
}

/**
 * 큰 금액을 만 단위로 축약
 * @param {number} amount
 * @returns {string} 예: "1.2만원"
 */
function formatAmountShort(amount) {
  if (amount >= 100000000) return (amount / 100000000).toFixed(1) + '억원';
  if (amount >= 10000) return (amount / 10000).toFixed(1) + '만원';
  return amount.toLocaleString('ko-KR') + '원';
}

// ── 날짜 유틸 ────────────────────────────────────────────────────────────────

/**
 * 오늘 날짜를 YYYY-MM-DD 형식으로 반환
 */
function getTodayString() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// ── API 유틸 ─────────────────────────────────────────────────────────────────

/**
 * fetch 래퍼 (JSON 응답 자동 파싱 + 에러 처리)
 */
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: { 'Content-Type': 'application/json' },
  };
  const res = await fetch(url, { ...defaults, ...options });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch (_) {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ── 금액 입력 자동 콤마 포맷 ────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // date 입력 기본값을 오늘로
  document.querySelectorAll('input[type=date]').forEach(el => {
    if (!el.value) el.value = getTodayString();
  });

  // 페이지 진입 페이드인
  document.querySelector('main')?.classList.add('fade-in');
});

// ── Chart.js 전역 기본 설정 ──────────────────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "'Noto Sans KR', sans-serif";
  Chart.defaults.color = '#6b7280';
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17,24,39,0.9)';
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.plugins.tooltip.titleFont = { size: 12, weight: '600' };
  Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
}
