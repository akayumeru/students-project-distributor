(function () {
  const form = document.getElementById('assignForm');
  if (!form) return;

  const fileInput = document.getElementById('assignFile');
  const btn = document.getElementById('assignBtn');
  const statusEl = document.getElementById('assignStatus');

  // Элементы блока валидации (используются при 422)
  const valBox = document.getElementById('assignValidation');
  const valSummary = document.getElementById('assignValidationSummary');
  const valErrorsBox = document.getElementById('assignValidationErrors');
  const valErrorsTbody = valErrorsBox?.querySelector('tbody');

  // Таблицы для успешного ответа
  const correctTbody = document.querySelector('#correctTable tbody');
  const incorrectTbody = document.querySelector('#incorrectTable tbody');
  const otherTbody = document.querySelector('#otherTable tbody');

  // Утилиты

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || '';
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function clearNode(el) {
    if (!el) return;
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function hideValidation() {
    if (valBox) valBox.hidden = true;
    if (valErrorsBox) valErrorsBox.hidden = true;
    clearNode(valErrorsTbody);
    if (valSummary) clearNode(valSummary);
  }

  function renderValidation(detail) {
    if (!valBox || !valSummary) return;

    valBox.hidden = false;
    valSummary.innerHTML = [
      `<div><strong>Всего строк:</strong> ${detail.rows_total ?? 0}</div>`,
      `<div><strong>Валидных строк:</strong> ${detail.rows_valid ?? 0}</div>`,
      `<div><strong>Невалидных строк:</strong> ${detail.rows_invalid ?? 0}</div>`,
      `<div><strong>Пропущен заголовок:</strong> ${detail.skipped_header ? 'да' : 'нет'}</div>`,
      `<div><strong>Статус:</strong> ${detail.ok ? 'OK' : 'Есть ошибки'}</div>`,
    ].join('\n');

    if (!valErrorsBox || !valErrorsTbody) return;
    clearNode(valErrorsTbody);

    const errors = Array.isArray(detail.errors) ? detail.errors : [];
    if (errors.length === 0) {
      valErrorsBox.hidden = true;
      return;
    }
    valErrorsBox.hidden = false;

    errors.forEach((e, i) => {
      const tr = document.createElement('tr');
      tr.innerHTML = [
        `<td>${i + 1}</td>`,
        `<td>${e.line ?? ''}</td>`,
        `<td>${e.column ?? ''}</td>`,
        `<td>${escapeHtml(e.field ?? '')}</td>`,
        `<td>${escapeHtml(e.message ?? '')}</td>`,
        `<td>${escapeHtml(e.value ?? '')}</td>`,
      ].join('');
      valErrorsTbody.appendChild(tr);
    });
  }

  function renderTeamsTable(tbody, teams, withTime) {
    if (!tbody) return;
    clearNode(tbody);
    const list = Array.isArray(teams) ? teams : [];
    list.forEach((team) => {
      const time = withTime ? (team.submission_time || '—') : '—';
      const members = Array.isArray(team.team_members) ? team.team_members.join(', ') : '';
      const project = team.assigned_project ?? '—';
      const tr = document.createElement('tr');
      tr.innerHTML = [
        `<td>${escapeHtml(time)}</td>`,
        `<td>${escapeHtml(members)}</td>`,
        `<td>${escapeHtml(String(project))}</td>`,
      ].join('');
      tbody.appendChild(tr);
    });
  }

  function renderSuccessPayload(payload) {
    const result = payload?.result || {};

    renderTeamsTable(correctTbody, result.valid_teams, /*withTime*/ true);
    renderTeamsTable(incorrectTbody, result.invalid_teams, /*withTime*/ true);
    renderTeamsTable(otherTbody, result.other_teams, /*withTime*/ false);

    const parts = [];
    if (typeof payload?.detail === 'string' && payload.detail) {
      parts.push(payload.detail);
    }
    if (typeof payload?.rows_processed === 'number') {
      parts.push(`Обработано строк: ${payload.rows_processed}`);
    }
    if (Array.isArray(result.unassigned_students) && result.unassigned_students.length > 0) {
      parts.push(`Нераспределённые участники: ${result.unassigned_students.join(', ')}`);
    }
    setStatus(parts.join(' | ') || 'Готово.');
  }

  form.addEventListener('submit', async (evt) => {
    evt.preventDefault();

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      setStatus('Выберите файл.');
      return;
    }

    hideValidation();
    clearNode(correctTbody);
    clearNode(incorrectTbody);
    clearNode(otherTbody);

    setStatus('Загрузка...');
    btn?.setAttribute('disabled', 'true');

    const fd = new FormData();
    fd.append('file', fileInput.files[0]);

    try {
      const resp = await fetch('/api/student-projects/assign', {
        method: 'POST',
        body: fd,
      });

      if (resp.status === 422) {
        let detail;
        try {
          const payload = await resp.json();
          detail = payload?.detail && typeof payload.detail === 'object'
            ? payload.detail
            : payload;
        } catch {
          setStatus('Файл не прошёл валидацию (ошибка парсинга ответа).');
          return;
        }
        setStatus('Файл не прошёл валидацию.');
        renderValidation(detail);
        return;
      }

      if (!resp.ok) {
        let msg = `Ошибка HTTP ${resp.status}`;
        try {
          const maybeJson = await resp.json();
          if (maybeJson?.detail) {
            msg += `: ${typeof maybeJson.detail === 'string'
              ? maybeJson.detail
              : JSON.stringify(maybeJson.detail)}`;
          }
        } catch {
          try {
            const text = await resp.text();
            if (text) msg += `: ${text}`;
          } catch { /* ignore */ }
        }
        setStatus(msg);
        return;
      }

      let data;
      try {
        data = await resp.json();
      } catch {
        setStatus('Ответ получен, но не JSON.');
        return;
      }
      renderSuccessPayload(data);

    } catch (err) {
      console.error(err);
      setStatus('Сетевая ошибка или сервер недоступен.');
    } finally {
      btn?.removeAttribute('disabled');
    }
  });
})();
