// TAC Generator Frontend Application Logic

let lastCompilation = null;
let simulationData = null;
let currentStepIndex = 0;

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupEditor();
  loadExamples();

  document.getElementById("compileBtn").addEventListener("click", () => compileCode());
  document.getElementById("simulateBtn").addEventListener("click", () => runSimulation());
  document.getElementById("clearBtn").addEventListener("click", () => clearEditor());
  document.getElementById("copyTacBtn").addEventListener("click", () => copyTac());
  document.getElementById("stepVmBtn").addEventListener("click", () => stepVm());
  document.getElementById("runAllVmBtn").addEventListener("click", () => runAllVm());
  document.getElementById("resetVmBtn").addEventListener("click", () => resetVm());

  // Compile initial code
  setTimeout(() => compileCode(), 200);
});

// Setup tab navigation
function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) {
        targetPane.classList.add("active");
      }
    });
  });
}

// Setup line numbers and key shortcuts in textarea
function setupEditor() {
  const textarea = document.getElementById("sourceCode");
  const lineNumbers = document.getElementById("lineNumbers");

  const updateLineNumbers = () => {
    const lines = textarea.value.split("\n").length;
    let numbers = "";
    for (let i = 1; i <= Math.max(lines, 1); i++) {
      numbers += i + "\n";
    }
    lineNumbers.textContent = numbers;
  };

  textarea.addEventListener("input", updateLineNumbers);
  textarea.addEventListener("scroll", () => {
    lineNumbers.scrollTop = textarea.scrollTop;
  });

  textarea.addEventListener("keydown", (e) => {
    // Ctrl + Enter to compile
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      compileCode();
    }
    // Tab key support
    if (e.key === "Tab") {
      e.preventDefault();
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      textarea.value = textarea.value.substring(0, start) + "    " + textarea.value.substring(end);
      textarea.selectionStart = textarea.selectionEnd = start + 4;
      updateLineNumbers();
    }
  });

  updateLineNumbers();
}

// Load preloaded examples
async function loadExamples() {
  try {
    const res = await fetch("/api/examples");
    const data = await res.json();
    const select = document.getElementById("exampleSelect");

    data.examples.forEach(ex => {
      const opt = document.createElement("option");
      opt.value = ex.name;
      opt.textContent = ex.title;
      select.appendChild(opt);
    });

    select.addEventListener("change", () => {
      const selected = data.examples.find(e => e.name === select.value);
      if (selected) {
        document.getElementById("sourceCode").value = selected.content;
        const event = new Event("input");
        document.getElementById("sourceCode").dispatchEvent(event);
        compileCode();
      }
    });
  } catch (err) {
    console.error("Failed to load examples", err);
  }
}

function clearEditor() {
  document.getElementById("sourceCode").value = "";
  const event = new Event("input");
  document.getElementById("sourceCode").dispatchEvent(event);
}

function showStatus(message, type = "success") {
  const alert = document.getElementById("statusAlert");
  alert.className = `status-alert ${type}`;
  alert.textContent = message;
  setTimeout(() => {
    alert.classList.add("hidden");
  }, 4000);
}

// Compile source code
async function compileCode() {
  const code = document.getElementById("sourceCode").value;
  const optimize = document.getElementById("optimizeCheckbox").checked;

  if (!code.trim()) {
    showStatus("Please enter source code to compile.", "error");
    return;
  }

  try {
    const res = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, optimize })
    });

    const data = await res.json();

    if (!data.success) {
      showStatus(data.error || "Compilation error", "error");
      return;
    }

    lastCompilation = data;
    showStatus("Compilation successful! Three Address Code generated.", "success");

    renderLinearTac(data.linear_tac);
    renderQuadruples(data.quadruples);
    renderTriples(data.triples);
    renderIndirectTriples(data.indirect_triples);
    renderAST(data.ast);
    renderCFG(data.cfg);
    renderOptimization(data);
  } catch (err) {
    showStatus("Network or server error during compilation.", "error");
    console.error(err);
  }
}

// 1. Render Linear TAC
function renderLinearTac(tacText) {
  const container = document.getElementById("linearTacOutput");
  const lines = tacText.split("\n");
  let html = "";
  lines.forEach((line, idx) => {
    html += `<span style="color:#64748b;user-select:none;">${String(idx + 1).padStart(3, " ")} | </span>${escapeHtml(line)}\n`;
  });
  container.innerHTML = `<code>${html}</code>`;
}

// 2. Render Quadruples
function renderQuadruples(quads) {
  const tbody = document.querySelector("#quadsTable tbody");
  tbody.innerHTML = "";

  if (!quads || quads.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No quadruples.</td></tr>`;
    return;
  }

  quads.forEach(q => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:#64748b;">${q.index}</td>
      <td style="color:#fbbf24;font-weight:bold;">${escapeHtml(q.op)}</td>
      <td style="color:#38bdf8;">${escapeHtml(q.arg1)}</td>
      <td style="color:#e879f9;">${escapeHtml(q.arg2)}</td>
      <td style="color:#34d399;font-weight:bold;">${escapeHtml(q.result)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 3. Render Triples
function renderTriples(triples) {
  const tbody = document.querySelector("#triplesTable tbody");
  tbody.innerHTML = "";

  if (!triples || triples.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No triples.</td></tr>`;
    return;
  }

  triples.forEach(t => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:#64748b;">${t.index}</td>
      <td style="color:#fbbf24;font-weight:bold;">${escapeHtml(t.op)}</td>
      <td style="color:#38bdf8;">${escapeHtml(t.arg1)}</td>
      <td style="color:#e879f9;">${escapeHtml(t.arg2)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 4. Render Indirect Triples
function renderIndirectTriples(indirect) {
  const tbody = document.querySelector("#indirectTable tbody");
  tbody.innerHTML = "";

  if (!indirect || indirect.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No indirect triples.</td></tr>`;
    return;
  }

  indirect.forEach(ind => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:#fbbf24;font-weight:bold;">${escapeHtml(ind.pointer)}</td>
      <td style="color:#64748b;">${escapeHtml(ind.statement)}</td>
      <td style="color:#38bdf8;">${escapeHtml(ind.op)}</td>
      <td style="color:#e879f9;">${escapeHtml(ind.arg1)}</td>
      <td style="color:#34d399;">${escapeHtml(ind.arg2)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 5. Render AST
function renderAST(astData) {
  const container = document.getElementById("astContainer");
  container.innerHTML = "";

  function createAstElement(node) {
    if (!node || typeof node !== "object") {
      return document.createTextNode(String(node));
    }

    const wrapper = document.createElement("div");
    wrapper.className = "tree-node";

    const typeSpan = document.createElement("span");
    typeSpan.className = "node-title";
    typeSpan.textContent = node.type || "Node";
    wrapper.appendChild(typeSpan);

    for (const [key, val] of Object.entries(node)) {
      if (key === "type") continue;

      const propDiv = document.createElement("div");
      propDiv.style.marginLeft = "12px";

      const propLabel = document.createElement("span");
      propLabel.className = "node-prop";
      propLabel.textContent = `${key}: `;
      propDiv.appendChild(propLabel);

      if (Array.isArray(val)) {
        if (val.length === 0) {
          const emptySpan = document.createElement("span");
          emptySpan.className = "node-val";
          emptySpan.textContent = "[]";
          propDiv.appendChild(emptySpan);
        } else {
          val.forEach(item => {
            propDiv.appendChild(createAstElement(item));
          });
        }
      } else if (val && typeof val === "object") {
        propDiv.appendChild(createAstElement(val));
      } else {
        const valSpan = document.createElement("span");
        valSpan.className = "node-val";
        valSpan.textContent = JSON.stringify(val);
        propDiv.appendChild(valSpan);
      }

      wrapper.appendChild(propDiv);
    }

    return wrapper;
  }

  container.appendChild(createAstElement(astData));
}

// 6. Render CFG
function renderCFG(cfgData) {
  const container = document.getElementById("cfgContainer");
  container.innerHTML = "";

  if (!cfgData || !cfgData.mermaid) {
    container.innerHTML = `<div class="empty-state">No CFG available.</div>`;
    return;
  }

  const mermaidDiv = document.createElement("div");
  mermaidDiv.className = "mermaid";
  mermaidDiv.textContent = cfgData.mermaid;
  container.appendChild(mermaidDiv);

  if (window.mermaid) {
    window.mermaid.initialize({ startOnLoad: false, theme: "dark" });
    window.mermaid.run({ nodes: [mermaidDiv] });
  }
}

// 7. Render Optimization Diff
function renderOptimization(data) {
  document.getElementById("diffOriginal").textContent = data.linear_tac || "";
  document.getElementById("diffOptimized").textContent = data.optimized_linear_tac || data.linear_tac || "";

  const statsContainer = document.getElementById("optStatsBadges");
  statsContainer.innerHTML = "";

  if (data.optimizer_stats) {
    const s = data.optimizer_stats;
    const chips = [
      { label: `Initial: ${s.initial_count} instrs`, color: "#64748b" },
      { label: `Optimized: ${s.final_count} instrs`, color: "#10b981" },
      { label: `Saved: ${s.instructions_reduced} instrs`, color: "#0284c7" },
      { label: `Constant Folds: ${s.constant_folds}`, color: "#f59e0b" },
      { label: `Algebraic Reductions: ${s.algebraic_simplifications}`, color: "#a855f7" },
      { label: `Copies Propagated: ${s.copy_propagations}`, color: "#38bdf8" },
      { label: `Dead Code Removed: ${s.dead_instructions_removed}`, color: "#f43f5e" }
    ];

    chips.forEach(c => {
      const chip = document.createElement("span");
      chip.className = "stat-chip";
      chip.style.backgroundColor = c.color;
      chip.textContent = c.label;
      statsContainer.appendChild(chip);
    });
  }
}

// 8. Run Simulation & Step Debugger
async function runSimulation() {
  const code = document.getElementById("sourceCode").value;
  const optimize = document.getElementById("optimizeCheckbox").checked;

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, optimize })
    });

    const data = await res.json();
    if (!data.success) {
      showStatus(data.error || "Simulation error", "error");
      return;
    }

    simulationData = data;
    currentStepIndex = 0;

    // Switch to VM Debugger Tab
    document.querySelectorAll(".tab-btn").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    document.querySelector('.tab-btn[data-tab="vmTab"]').classList.add("active");
    document.getElementById("vmTab").classList.add("active");

    renderVmInstructions();
    updateVmState();
    showStatus(`Simulation initialized: ${data.total_steps} execution steps.`, "success");
  } catch (err) {
    showStatus("Failed to run simulation.", "error");
    console.error(err);
  }
}

function renderVmInstructions() {
  const container = document.getElementById("vmInstructionList");
  container.innerHTML = "";

  if (!lastCompilation) return;
  const targetTac = (document.getElementById("optimizeCheckbox").checked && lastCompilation.optimized_linear_tac)
    ? lastCompilation.optimized_linear_tac
    : lastCompilation.linear_tac;

  const lines = targetTac.split("\n");
  lines.forEach((line, idx) => {
    const row = document.createElement("div");
    row.className = "vm-instr-row";
    row.id = `vm-instr-${idx}`;
    row.innerHTML = `<span class="vm-instr-ip">${idx}</span><span>${escapeHtml(line)}</span>`;
    container.appendChild(row);
  });
}

function updateVmState() {
  if (!simulationData || simulationData.trace.length === 0) return;

  const total = simulationData.trace.length;
  document.getElementById("stepCounter").textContent = `Step ${currentStepIndex} / ${total}`;

  // Highlight active instruction row
  document.querySelectorAll(".vm-instr-row").forEach(r => r.classList.remove("active"));

  let userVars = {};
  if (currentStepIndex > 0) {
    const stepObj = simulationData.trace[currentStepIndex - 1];
    userVars = stepObj.user_vars || {};
    const activeRow = document.getElementById(`vm-instr-${stepObj.ip}`);
    if (activeRow) {
      activeRow.classList.add("active");
      activeRow.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }

  // Render variables table
  const tbody = document.querySelector("#vmVarTable tbody");
  tbody.innerHTML = "";
  const varKeys = Object.keys(userVars);
  if (varKeys.length === 0) {
    tbody.innerHTML = `<tr><td colspan="2" class="empty-state">No variables yet.</td></tr>`;
  } else {
    varKeys.sort().forEach(k => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td style="color:#38bdf8;font-weight:bold;">${escapeHtml(k)}</td><td style="color:#34d399;">${escapeHtml(String(userVars[k]))}</td>`;
      tbody.appendChild(tr);
    });
  }

  // Render logs
  const logsEl = document.getElementById("vmLogs");
  if (simulationData.logs && simulationData.logs.length > 0) {
    logsEl.textContent = simulationData.logs.join("\n");
  } else {
    logsEl.textContent = "[No standard output]";
  }
}

function stepVm() {
  if (!simulationData || simulationData.trace.length === 0) return;
  if (currentStepIndex < simulationData.trace.length) {
    currentStepIndex++;
    updateVmState();
  }
}

function runAllVm() {
  if (!simulationData || simulationData.trace.length === 0) return;
  currentStepIndex = simulationData.trace.length;
  updateVmState();
}

function resetVm() {
  currentStepIndex = 0;
  updateVmState();
}

function copyTac() {
  if (!lastCompilation) return;
  const tac = lastCompilation.linear_tac;
  navigator.clipboard.writeText(tac).then(() => {
    showStatus("Three Address Code copied to clipboard!", "success");
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
