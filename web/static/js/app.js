(() => {
    'use strict';

    const editor = document.getElementById('code-editor');
    const lineNumbers = document.getElementById('line-numbers');
    const cursorPosition = document.getElementById('cursor-position');

    const newFileBtn = document.getElementById('new-file-btn');
    const openFileBtn = document.getElementById('open-file-btn');
    const saveFileBtn = document.getElementById('save-file-btn');
    const runBtn = document.getElementById('run-btn');
    const reportsBtn = document.getElementById('reports-btn');
    const fileInput = document.getElementById('file-input');

    const fileName = document.getElementById('file-name');
    const dirtyIndicator = document.getElementById('dirty-indicator');
    const saveStatus = document.getElementById('save-status');

    const consoleOutput = document.getElementById('console-output');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const executionTime = document.getElementById('execution-time');

    const reportsPanel = document.getElementById('reports-panel');
    const tabButtons = [...document.querySelectorAll('.tab-btn')];

    const errorCount = document.getElementById('error-count');
    const errorsEmpty = document.getElementById('errors-empty');
    const errorsTableWrapper = document.getElementById('errors-table-wrapper');
    const errorsBody = document.getElementById('errors-body');

    const symbolsEmpty = document.getElementById('symbols-empty');
    const symbolsTableWrapper = document.getElementById('symbols-table-wrapper');
    const symbolsBody = document.getElementById('symbols-body');

    const astEmpty = document.getElementById('ast-empty');
    const astFrame = document.getElementById('ast-frame');
    const openAstBtn = document.getElementById('open-ast-btn');

    let currentFileName = 'main.ox';
    let dirty = false;
    let hasExecuted = false;

    const DEFAULT_SOURCE = `fn main() {
    println!("Hola, OxigenScript!");
}`;

    function setDirty(value) {
        dirty = Boolean(value);
        dirtyIndicator.classList.toggle('dirty', dirty);

        saveStatus.textContent = dirty
            ? 'Cambios sin guardar'
            : 'Archivo sincronizado';
    }

    function setFileName(name) {
        currentFileName = name || 'main.ox';
        fileName.textContent = currentFileName;
    }

    function updateLineNumbers() {
        const count = Math.max(
            1,
            editor.value.split('\n').length,
        );

        lineNumbers.textContent = Array.from(
            { length: count },
            (_, index) => String(index + 1),
        ).join('\n');
    }

    function syncEditorScroll() {
        lineNumbers.scrollTop = editor.scrollTop;
    }

    function updateCursorPosition() {
        const before = editor.value.slice(
            0,
            editor.selectionStart,
        );

        const lines = before.split('\n');

        const line = lines.length;
        const column = lines[lines.length - 1].length + 1;

        cursorPosition.textContent = `Ln ${line}, Col ${column}`;
    }

    function setStatus(kind, text, timeText = '—') {
        statusDot.className = `status-dot ${kind}`;
        statusText.textContent = text;
        executionTime.textContent = timeText;
    }

    function switchTab(name) {
        for (const button of tabButtons) {
            const active = button.dataset.tab === name;

            button.classList.toggle(
                'active',
                active,
            );

            button.setAttribute(
                'aria-selected',
                String(active),
            );
        }

        for (const pane of document.querySelectorAll('.tab-pane')) {
            pane.classList.toggle(
                'active',
                pane.id === `tab-${name}`,
            );
        }
    }

    function clearReports() {
        errorCount.textContent = '0';

        errorsBody.replaceChildren();
        errorsEmpty.classList.remove('hidden');
        errorsTableWrapper.classList.add('hidden');

        symbolsBody.replaceChildren();
        symbolsEmpty.classList.remove('hidden');
        symbolsTableWrapper.classList.add('hidden');

        astFrame.classList.add('hidden');
        astFrame.removeAttribute('src');
        astEmpty.classList.remove('hidden');

        hasExecuted = false;
    }

    function createCell(value, code = false) {
        const td = document.createElement('td');

        if (code) {
            const codeElement = document.createElement('code');
            codeElement.textContent = value ?? '';
            td.appendChild(codeElement);
        } else {
            td.textContent = value ?? '';
        }

        return td;
    }

    function renderErrors(errors) {
        errorsBody.replaceChildren();
        errorCount.textContent = String(errors.length);

        if (!errors.length) {
            errorsEmpty.textContent = 'No se encontraron errores.';
            errorsEmpty.classList.remove('hidden');
            errorsTableWrapper.classList.add('hidden');
            return;
        }

        errorsEmpty.classList.add('hidden');
        errorsTableWrapper.classList.remove('hidden');

        for (const error of errors) {
            const row = document.createElement('tr');

            row.append(
                createCell(error.no),
                createCell(error.tipo),
                createCell(error.descripcion),
                createCell(error.linea),
                createCell(error.columna),
                createCell(error.fragmento, true),
            );

            errorsBody.appendChild(row);
        }
    }

    function renderSymbols(symbols) {
        symbolsBody.replaceChildren();

        if (!symbols.length) {
            symbolsEmpty.textContent = 'No hay símbolos registrados.';
            symbolsEmpty.classList.remove('hidden');
            symbolsTableWrapper.classList.add('hidden');
            return;
        }

        symbolsEmpty.classList.add('hidden');
        symbolsTableWrapper.classList.remove('hidden');

        for (const symbol of symbols) {
            const row = document.createElement('tr');

            row.append(
                createCell(symbol.no),
                createCell(symbol.identificador),
                createCell(symbol.categoria),
                createCell(symbol.tipo),
                createCell(symbol.ambito),
                createCell(symbol.linea),
                createCell(symbol.valor, true),
            );

            symbolsBody.appendChild(row);
        }
    }

    function renderAst(success) {
        if (!success) {
            astFrame.classList.add('hidden');
            astEmpty.textContent = (
                'El AST no se muestra porque el programa contiene errores.'
            );
            astEmpty.classList.remove('hidden');
            return;
        }

        astEmpty.classList.add('hidden');
        astFrame.classList.remove('hidden');

        astFrame.src = (
            `/api/reports/ast/?t=${Date.now()}`
        );
    }

    function formatConsole(data) {
        const parts = [];

        if (data.output) {
            parts.push(data.output);
        }

        if (data.errors?.length) {
            if (parts.length) {
                parts.push('');
            }

            parts.push(
                `[${data.errors.length} error(es) detectado(s)]`,
            );

            for (const error of data.errors) {
                parts.push(
                    `[Error ${error.tipo}] Línea ${error.linea}, Columna ${error.columna}`,
                );

                parts.push(
                    error.descripcion,
                );
            }
        }

        if (!parts.length) {
            parts.push(
                data.success
                    ? 'Ejecución finalizada sin salida.'
                    : 'La ejecución no produjo salida.',
            );
        }

        return parts.join('\n');
    }

    async function executeProgram() {
        runBtn.disabled = true;
        setStatus('running', 'Ejecutando…', '—');

        consoleOutput.textContent = 'Procesando programa…';

        const startedAt = performance.now();

        try {
            const response = await fetch(
                '/api/execute/',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: editor.value,
                    }),
                },
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message || `HTTP ${response.status}`,
                );
            }

            const elapsed = performance.now() - startedAt;
            const timeText = `${elapsed.toFixed(1)} ms`;

            consoleOutput.textContent = formatConsole(data);

            renderErrors(
                data.errors || [],
            );

            renderSymbols(
                data.symbols || [],
            );

            renderAst(
                Boolean(data.success),
            );

            hasExecuted = true;

            if (data.success) {
                setStatus(
                    'success',
                    'Ejecución exitosa',
                    timeText,
                );

                switchTab('symbols');
            } else {
                setStatus(
                    'error',
                    'Ejecución con errores',
                    timeText,
                );

                switchTab('errors');
            }
        } catch (error) {
            const elapsed = performance.now() - startedAt;

            consoleOutput.textContent = (
                'No fue posible ejecutar el programa.\n'
                + String(error.message || error)
            );

            setStatus(
                'error',
                'Error de conexión',
                `${elapsed.toFixed(1)} ms`,
            );
        } finally {
            runBtn.disabled = false;
        }
    }

    function newFile() {
        if (
            dirty
            && !window.confirm(
                'Hay cambios sin guardar. ¿Crear un archivo nuevo de todas formas?',
            )
        ) {
            return;
        }

        editor.value = DEFAULT_SOURCE;
        setFileName('main.ox');
        setDirty(false);

        consoleOutput.textContent = 'Archivo nuevo creado.';
        setStatus('idle', 'Listo', '—');

        clearReports();
        updateLineNumbers();
        updateCursorPosition();

        editor.focus();
    }

    function openFile() {
        fileInput.value = '';
        fileInput.click();
    }

    async function loadSelectedFile() {
        const file = fileInput.files?.[0];

        if (!file) {
            return;
        }

        try {
            const text = await file.text();

            editor.value = text;
            setFileName(file.name);
            setDirty(false);

            consoleOutput.textContent = `Archivo abierto: ${file.name}`;
            setStatus('idle', 'Archivo abierto', '—');

            clearReports();
            updateLineNumbers();
            updateCursorPosition();

            editor.focus();
        } catch (error) {
            consoleOutput.textContent = (
                `No fue posible abrir el archivo: ${error.message || error}`
            );

            setStatus('error', 'Error al abrir', '—');
        }
    }

    function saveFile() {
        const blob = new Blob(
            [editor.value],
            {
                type: 'text/plain;charset=utf-8',
            },
        );

        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');

        anchor.href = url;
        anchor.download = currentFileName || 'main.ox';

        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();

        URL.revokeObjectURL(url);

        setDirty(false);
        saveStatus.textContent = `Descargado: ${anchor.download}`;
    }

    function handleTabKey(event) {
        if (event.key !== 'Tab') {
            return;
        }

        event.preventDefault();

        const start = editor.selectionStart;
        const end = editor.selectionEnd;

        editor.setRangeText(
            '    ',
            start,
            end,
            'end',
        );

        setDirty(true);
        updateLineNumbers();
        updateCursorPosition();
    }

    editor.addEventListener(
        'input',
        () => {
            setDirty(true);
            updateLineNumbers();
            updateCursorPosition();
        },
    );

    editor.addEventListener(
        'scroll',
        syncEditorScroll,
    );

    editor.addEventListener(
        'click',
        updateCursorPosition,
    );

    editor.addEventListener(
        'keyup',
        updateCursorPosition,
    );

    editor.addEventListener(
        'keydown',
        handleTabKey,
    );

    newFileBtn.addEventListener(
        'click',
        newFile,
    );

    openFileBtn.addEventListener(
        'click',
        openFile,
    );

    fileInput.addEventListener(
        'change',
        loadSelectedFile,
    );

    saveFileBtn.addEventListener(
        'click',
        saveFile,
    );

    runBtn.addEventListener(
        'click',
        executeProgram,
    );

    reportsBtn.addEventListener(
        'click',
        () => {
            reportsPanel.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
            });

            if (!hasExecuted) {
                switchTab('errors');
            }
        },
    );

    for (const button of tabButtons) {
        button.addEventListener(
            'click',
            () => switchTab(
                button.dataset.tab,
            ),
        );
    }
    
    openAstBtn.addEventListener(
        'click',
        () => {
            if (
                !hasExecuted
                || astFrame.classList.contains('hidden')
            ) {
                consoleOutput.textContent = (
                    'Primero ejecuta un programa válido para generar el AST.'
                );

                return;
            }

            window.open(
                `/api/reports/ast/?t=${Date.now()}`,
                '_blank',
            );
        },
    );

    window.addEventListener(
        'keydown',
        (event) => {
            if (
                event.ctrlKey
                && event.key.toLowerCase() === 's'
            ) {
                event.preventDefault();
                saveFile();
            }

            if (
                event.ctrlKey
                && event.key.toLowerCase() === 'o'
            ) {
                event.preventDefault();
                openFile();
            }

            if (
                event.ctrlKey
                && event.key === 'Enter'
            ) {
                event.preventDefault();
                executeProgram();
            }
        },
    );

    updateLineNumbers();
    updateCursorPosition();
    setDirty(false);
})();
